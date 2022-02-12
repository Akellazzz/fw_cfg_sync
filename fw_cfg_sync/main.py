import os
import sys
from this import d
from functions.connections import BaseConnection, Multicontext
from functions.load_config import load_inventory, load_mail_config
from functions.send_mail import send_mail
from functions.find_delta import create_diff_files
from functions.check_context_role import check_context_role
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

    # # путь к основной директории
    # main_dir = os.path.dirname(sys.argv[0])

    args = getargs()
    datetime_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    logfilename = f"fw_cfg_sync_{datetime_now}.log"
    logfile = os.path.join(app_log_dir, logfilename)
    log_config = {
        "handlers": [
            {
                "sink": logfile,
                # "sink": f"{logs_dir}" + "/fw_cfg_sync_{time}.log",
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
    # 2022-01-09T19:43:02.912262+0300 INFO No matter added sinks, this message is not displayed
    # logger.remove()

    if not app_config_path:
        msg = "В переменных среды не найдена FW-CFG-SYNC_APP_CONFIG, указывающая путь к конфигурации программы"
        logger.error(msg)
        sys.exit(msg)

    app_config = os.path.join(app_config_path, "app_config.yaml")
    mail_config = load_mail_config(app_config)
    mail_text = 'Лог выполнения и дельты конфигов во вложении.'
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
        if sorted(inv.contexts_role_check) != sorted(fw.contexts):
            msg = f'В inventory заданы контексты {sorted(inv.contexts_role_check)}, но на МСЭ {fw.name} найдены контексты {sorted(fw.contexts)}'
            mail_text += f'{msg}<br>'
            logger.warning(msg)

        if not (set(fw.contexts).issubset(set(inv.contexts_role_check))):
            # TODO описать ошибку
            logger.warning("set(inv.contexts_role_check) not in set(fw.contexts)")
            logger.warning(f"{set(inv.contexts_role_check)} not in {set(fw.contexts)}")
            sys.exit()

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
        firewalls, error = check_context_role(environment, app_config, firewalls, routers, inv)
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
    firewalls = create_diff_files(firewalls, datetime_now)

    for fw in firewalls:
        for context in fw.contexts:
            if fw.contexts[context].get('delta_path'):
                attached_files.append(fw.contexts[context].get('delta_path'))

    # for fw in firewalls:
    #     mail_text += f'{msg}<br>'

    #     for context in fw.contexts:
    #              mail_text += f'{msg}<br>'
    mail_config.subject = f'Отчет о синхронизации конфигураций {firewalls[0].name} и {firewalls[1].name}'
    send_mail(mail_text, files=attached_files, **mail_config.dict())
    pass


if __name__ == "__main__":
    main()
