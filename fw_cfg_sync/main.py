import os
import sys
from functions.connections import BaseConnection, Multicontext
from functions.load_config import load_inventory, load_mail_config
from functions.send_mail import send_mail
from functions.find_delta import create_diff_files
from functions.check_context_role import check_context_role
from functions.create_commands import create_commands_for_reserve_context
from argparse import ArgumentParser, RawTextHelpFormatter
from datetime import datetime
from loguru import logger


def getargs():
    modes = ["sync", "check"]
    reports = ["cli", "mail"]
    parser = ArgumentParser(
        description=f"""Программа синхронизации конфигураций МСЭ между площадками. 
Документация - wiki""",
        formatter_class=RawTextHelpFormatter,
    )  # TODO
    parser.add_argument(
        "-v",
        "--verbose",
        help="Уровень логирования - DEBUG (по умолчанию - INFO)",
        action="store_true",
    )
    parser.add_argument(
        "-f",
        dest="filename",
        type=str,
        help="инвентарный файл из каталога /inventory",
        required=True,
    )

    parser.add_argument(
        "-s", 
        dest="sync_mode", 
        help="выравнивание конфигурации резервного контекста (по умолчанию только формируется отчет)", 
        action="store_true",
    )
    # parser.add_argument("-m", dest="mode", type=str, help=f"{modes}", required=True)
    # parser.add_argument("-r", dest="report", type=str, help=f"{reports}", required=True)
    return parser.parse_args()


def get_devices_by_function(inv, device_function: str) -> tuple:
    """ """
    devices = []

    for device in inv.devices:
        kwargs = {'name': inv.devices[device].get("name"),
            'host': inv.devices[device]["connection"]["host"],
            'credentials': inv.devices[device]["connection"]["credentials"],
            'device_type': inv.devices[device]["connection"]["device_type"],
            'device_function': inv.devices[device]["device_function"],
            'fast_cli': inv.devices[device]["connection"]["fast_cli"],
            'enable_required': inv.devices[device]["connection"]["enable_required"]}

        if inv.multicontext == True:
            if inv.devices[device]["device_function"] == device_function and device_function == "fw":
                devices.append(
                    Multicontext(**kwargs)
                )
        if inv.devices[device]["device_function"] == device_function and device_function == "router":
            devices.append(BaseConnection(**kwargs))
    return tuple(devices)


def main():

    # среда dev/prod
    environment = os.environ.get("FW-CFG-SYNC_ENVIRONMENT")

    # путь к конфигурации программы
    app_config_path = os.environ.get("FW-CFG-SYNC_APP_CONFIG")

    # директория для сохранения логов
    app_log_dir = os.environ.get("FW-CFG-SYNC_LOGDIR")


    args = getargs()
    datetime_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


    logfilename = f"fw_cfg_sync_{datetime_now}.log"
    logfile = os.path.join(app_log_dir, logfilename)
    log_config = {
        "handlers": [
            {
                "sink": logfile,
                "retention": "30 days",
                "backtrace": True,
                "diagnose": True,
                "encoding": "utf-8",
            },
        ]
    }
    logger.configure(**log_config)
    if args.verbose:
        logger.add(sys.stdout, level="DEBUG")
    else:
        logger.add(sys.stdout, format="{message}", level="INFO")


    if not app_config_path:
        msg = "В переменных среды не найдена FW-CFG-SYNC_APP_CONFIG, указывающая путь к конфигурации программы"
        logger.error(msg)
        sys.exit(msg)


    app_config = os.path.join(app_config_path, "app_config.yaml")
    mail_config = load_mail_config(app_config)
    mail_text = 'Лог выполнения и дельты конфигов во вложении.<br>'
    attached_files = [logfile]

    inv_path = os.path.join(app_config_path, "inventory", args.filename)
    inv = load_inventory(inv_path)

    firewalls = get_devices_by_function(inv, 'fw')
    assert len(firewalls) == 2

    if inv.prerequisites.get('check_route'):
        routers = get_devices_by_function(inv, 'router')
        assert routers
        devices = firewalls + routers
    else:
        devices = firewalls

    if environment != "dev":
        for device in devices:
            device.check_reachability()
            if not device.is_reachable:
                mail_text += f"Не удалось подключиться к {device.name}"
                send_mail(mail_text, files=[logfile], **mail_config.dict())
                sys.exit(mail_text)

    for fw in firewalls:
        fw.get_contexts()
        inv_contexts = sorted(inv.contexts_role_check)
        if inv_contexts != sorted(fw.contexts):
            msg = f'Список контекстов в inventory: {inv_contexts} не совпадает со списком контекстов на МСЭ {fw.name}: {sorted(fw.contexts)}'
            # mail_text += f'{msg}<br>'
            logger.warning(msg)

            if inv.prerequisites.get('inventory_must_contain_all_contexts'):
                logger.warning('В app_config флаг inventory_must_contain_all_contexts: True - Выход')
                sys.exit()
            else:
                msg = f'Скрипт продолжит работу с контекстами {inv_contexts}'
                logger.warning(msg)
                fw.contexts = dict.fromkeys(inv_contexts)


    if set(firewalls[0].contexts) ^ set(firewalls[1].contexts):
        # Разные контексты 
        common_contexts = set(firewalls[0].contexts).intersection(set(firewalls[1].contexts))
        common_contexts = sorted(list(common_contexts))
        firewalls[0].contexts = common_contexts
        firewalls[1].contexts = common_contexts
        msg = f'На {firewalls[0].name} заданы контексты {firewalls[0].contexts}. На {firewalls[1].name} заданы контексты {firewalls[1].contexts}. В работу взяты общие контекты {common_contexts}'
        mail_text += f'{msg}<br>'
        logger.warning(msg)

    #     for context in fw.contexts:
    #         fw.is_active = check_role(context)  # if it's active site sets fw.is_active = True  else False

    if inv.prerequisites.get('check_route'):

        # устанавливает роль контекста
        # fw.contexts[context] = {"role": "active"}
        # fw.contexts[context] = {"role": "reserve"}
        firewalls, error = check_context_role(firewalls, routers, inv)
        if error:
            send_mail(error, files=attached_files, **mail_config.dict())
            sys.exit()
    else:
        # TODO статически задавать роли
        sys.exit()

    for fw in firewalls:
        for context in fw.contexts:
            fw.get_context_backup(context)
            fw.save_backup_to_file(context, datetime_now)


    # active_fw, standby_fw, attached_files = create_diff_files(
    #     attached_files, active_fw, standby_fw, datetime_now
    # )

    # если есть дельта, сохраняет ее в fw.contexts[context]["delta"]
    # и в файл, путь к которому указывается в fw.contexts[context]["delta_path"]
    firewalls = create_diff_files(firewalls, datetime_now)

    # генерирует команды для выравнивания резервного контекста и добавляет их в fw.contexts[context]["commands"]
    # путь к файлу с командами сохраняется в fw.contexts[context]["commands_path"]
    create_commands_for_reserve_context(firewalls, datetime_now)     


    # отправка команд для выравнивания конфигурации на контекст резервного МСЭ
    if args.sync_mode:
        for fw in firewalls:
            for context in fw.contexts:
                config_set = []
                if fw.contexts[context].get('commands'):
                    config_set = fw.contexts[context].get('commands')
                    fw.send_config_set_to_context(config_set, context, datetime_now)

                    filename = f'{fw.name}-{context}_{datetime_now}_configuration_log.txt'
                    msg = f'Внесены изменения в конфигурацию {fw.name}/{context}. <br>Лог в файле {filename}.'
                    mail_text += f'{msg}<br>'
                    logger.warning(msg)

                # вложения в письмо с отчетом
                if fw.contexts[context].get('delta_path'):
                    attached_files.append(fw.contexts[context].get('delta_path'))
                if fw.contexts[context].get('commands_path'):
                    attached_files.append(fw.contexts[context].get('commands_path'))

        # повторное снятие бэкапа и вычисление дельты после внесения изменений
        datetime_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        for fw in firewalls:
            for context in fw.contexts:
                if fw.contexts[context].get('commands'):

                    fw.get_context_backup(context)
                    fw.save_backup_to_file(context, datetime_now)
        firewalls = create_diff_files(firewalls, datetime_now)


    # формирование и отправка отчета на почту
    for fw in firewalls:
        for context in fw.contexts:
            if fw.contexts[context].get('delta_path') and fw.contexts[context].get('delta_path') not in attached_files:
                attached_files.append(fw.contexts[context].get('delta_path'))
            if fw.contexts[context].get('commands_path') and fw.contexts[context].get('commands_path') not in attached_files:
                attached_files.append(fw.contexts[context].get('commands_path'))

    mail_config.subject = f'Отчет о синхронизации конфигураций {firewalls[0].name} и {firewalls[1].name}'
    send_mail(mail_text, files=attached_files, **mail_config.dict())
    pass


if __name__ == "__main__":
    main()
