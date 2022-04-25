import os
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from datetime import datetime

from loguru import logger

from functions.check_context_role import check_context_role
from functions.connections import BaseConnection, Multicontext
from functions.create_commands import create_commands
from functions.find_delta import create_diff_files
from functions.load_config import load_inventory, load_mail_config
from functions.send_mail import send_mail

datetime_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


PARENT_DIR = "FW-CFG-SYNC"

# среда dev/prod
ENVIRONMENT = os.environ.get(f"{PARENT_DIR}_ENVIRONMENT")

# путь к конфигурации программы
APP_CONFIG_PATH = os.environ.get(f"{PARENT_DIR}_APP_CONFIG")

# директория для сохранения логов
APP_LOG_DIR = os.environ.get(f"{PARENT_DIR}_LOGDIR")

# директория для сохранения конфигов МСЭ
BACKUP_DIR = os.environ.get(f"{PARENT_DIR}_BACKUPS")


def check_env_vars():
    for var in ENVIRONMENT, APP_CONFIG_PATH, APP_LOG_DIR, BACKUP_DIR:
        if not var:
            msg = f"В переменных среды не найдена обязательная переменная {var}"
            logger.error(msg)
            sys.exit(msg)


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
        kwargs = {
            "name": inv.devices[device].get("name"),
            "host": inv.devices[device]["connection"]["host"],
            "credentials": inv.devices[device]["connection"]["credentials"],
            "device_type": inv.devices[device]["connection"]["device_type"],
            "device_function": inv.devices[device]["device_function"],
            "fast_cli": inv.devices[device]["connection"]["fast_cli"],
            "enable_required": inv.devices[device]["connection"]["enable_required"],
        }

        if inv.multicontext == True:
            if inv.devices[device]["device_function"] == device_function == "fw":
                devices.append(Multicontext(**kwargs))
        if inv.devices[device]["device_function"] == device_function == "router":
            router_log_dir = os.path.join(APP_LOG_DIR, kwargs["name"])

            if not os.path.exists(router_log_dir):
                os.mkdir(router_log_dir)
                logger.info(f"Создана директория {router_log_dir} ")

            filename = f'{kwargs.get("name")}_{datetime_now}.txt'

            kwargs["session_log"] = os.path.join(router_log_dir, filename)

            devices.append(BaseConnection(**kwargs))
    return tuple(devices)


def _create_commands_for_reserve_context(firewalls):
    def read_config(path: str) -> list:
        with open(path) as f:
            return [i.rstrip() for i in f.readlines()]

    for context in firewalls[0].contexts:

        if (
            firewalls[0].contexts[context].get("role") == "active"
            and firewalls[1].contexts[context].get("role") == "reserve"
        ):
            active = firewalls[0]
            reserve = firewalls[1]
        elif (
            firewalls[0].contexts[context].get("role") == "reserve"
            and firewalls[1].contexts[context].get("role") == "active"
        ):
            active = firewalls[1]
            reserve = firewalls[0]
        else:
            logger.error("Ошибка при определении ролей")
            raise ValueError("Ошибка при определении ролей")

        active_delta = active.contexts[context].get("delta_path")
        reserve_delta = reserve.contexts[context].get("delta_path")
        act_config_list = read_config(active.contexts[context].get("backup_path"))
        res_config_list = read_config(reserve.contexts[context].get("backup_path"))
        act_delta_list = read_config(active_delta) if active_delta else []
        res_delta_list = read_config(reserve_delta) if reserve_delta else []

        if active_delta or reserve_delta:
            commands_for_reserve_context = create_commands(
                act_config_list, res_config_list, act_delta_list, res_delta_list
            )
            reserve.contexts[context]["commands"] = commands_for_reserve_context
            # print(commands_for_reserve_context)

            commands_filename = f"{reserve.name}-{context}_{datetime_now}_commands.txt"
            commands_fullpath = os.path.join(
                BACKUP_DIR, reserve.name, commands_filename
            )
            with open(commands_fullpath, "w") as f:
                f.write("\n".join(commands_for_reserve_context))
            logger.info(
                f"Команды для {reserve.name}-{context} сохранены в файл {commands_fullpath}"
            )
            reserve.contexts[context]["commands_path"] = commands_fullpath
        else:
            logger.info(
                f"Команды для контекста {reserve.name}-{context} не созданы, т. к. отсутствует дельта"
            )


def main():
    check_env_vars()
    args = getargs()

    logfile = os.path.join(APP_LOG_DIR, f"fw_cfg_sync_{datetime_now}.log")
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

    mail_config = load_mail_config(os.path.join(APP_CONFIG_PATH, "app_config.yaml"))
    mail_text = "Лог выполнения и дельты конфигов во вложении.<br>"
    attached_files = [logfile]

    inv_path = os.path.join(APP_CONFIG_PATH, "inventory", args.filename)
    inv = load_inventory(inv_path)

    firewalls = get_devices_by_function(inv, "fw")
    assert len(firewalls) == 2

    if inv.prerequisites.get("check_route"):
        routers = get_devices_by_function(inv, "router")
        assert routers
        devices = firewalls + routers
    else:
        devices = firewalls

    if ENVIRONMENT != "dev":
        for device in devices:
            device.check_reachability()
            if not device.is_reachable:
                mail_text += f"Не удалось подключиться к {device.name}"
                send_mail(mail_text, files=attached_files, **mail_config.dict())
                sys.exit(mail_text)

    for fw in firewalls:
        fw.get_contexts()
        if fw.contexts == []:
            logger.warning(
                f"Не удалось сформировать список контекстов МСЭ {fw.name}"
            )
            sys.exit()

        inv_contexts = sorted(inv.contexts)
        if inv_contexts != sorted(fw.contexts):
            msg = f"Список контекстов в inventory: {inv_contexts} не совпадает со списком контекстов на МСЭ {fw.name}: {sorted(fw.contexts)}"
            # mail_text += f'{msg}<br>'
            logger.warning(msg)

            if inv.prerequisites.get("inventory_must_contain_all_contexts"):
                logger.warning(
                    "В app_config флаг inventory_must_contain_all_contexts: True - Выход"
                )
                sys.exit()
            else:
                msg = f"Скрипт продолжит работу с контекстами {inv_contexts}"
                logger.warning(msg)
                fw.contexts = dict.fromkeys(inv_contexts)

    if set(firewalls[0].contexts) ^ set(firewalls[1].contexts):
        # Разные контексты
        common_contexts = set(firewalls[0].contexts).intersection(
            set(firewalls[1].contexts)
        )
        firewalls[0].contexts = firewalls[1].contexts = sorted(list(common_contexts))

        msg = f"На {firewalls[0].name} заданы контексты {firewalls[0].contexts}. На {firewalls[1].name} заданы контексты {firewalls[1].contexts}. В работу взяты общие контекты {common_contexts}"
        mail_text += f"{msg}<br>"
        logger.warning(msg)

    #     for context in fw.contexts:
    #         fw.is_active = check_role(context)  # if it's active site sets fw.is_active = True  else False

    if inv.prerequisites.get("check_route"):

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
    _create_commands_for_reserve_context(firewalls)

    # отправка команд для выравнивания конфигурации на контекст резервного МСЭ
    if args.sync_mode:
        for fw in firewalls:
            for context in fw.contexts:
                config_set = []
                if fw.contexts[context].get("commands") and inv.contexts.context.get("working_mode") == "sync":
                    config_set = fw.contexts[context].get("commands")
                    fw.send_config_set_to_context(config_set, context, datetime_now)

                    filename = (
                        f"{fw.name}-{context}_{datetime_now}_configuration_log.txt"
                    )
                    msg = f"Внесены изменения в конфигурацию {fw.name}/{context}. <br>Лог в файле {filename}."
                    mail_text += f"{msg}<br>"
                    logger.warning(msg)

                # вложения в письмо с отчетом
                if fw.contexts[context].get("delta_path"):
                    attached_files.append(fw.contexts[context].get("delta_path"))
                if fw.contexts[context].get("commands_path"):
                    attached_files.append(fw.contexts[context].get("commands_path"))

        # повторное снятие бэкапа и вычисление дельты после внесения изменений
        datetime_after_change = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        for fw in firewalls:
            for context in fw.contexts:
                if fw.contexts[context].get("commands") and inv.contexts.context.get("working_mode") == "sync":

                    fw.get_context_backup(context)
                    fw.save_backup_to_file(context, datetime_after_change)
        firewalls = create_diff_files(firewalls, datetime_after_change)

    # формирование и отправка отчета на почту
    for fw in firewalls:
        for context in fw.contexts:
            if (
                fw.contexts[context].get("delta_path")
                and fw.contexts[context].get("delta_path") not in attached_files
            ):
                attached_files.append(fw.contexts[context].get("delta_path"))
            if (
                fw.contexts[context].get("commands_path")
                and fw.contexts[context].get("commands_path") not in attached_files
            ):
                attached_files.append(fw.contexts[context].get("commands_path"))

    mail_config.subject = (
        f"Отчет о синхронизации конфигураций {firewalls[0].name} и {firewalls[1].name}"
    )
    send_mail(mail_text, files=attached_files, **mail_config.dict())
    pass


if __name__ == "__main__":
    main()
