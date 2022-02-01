import os
import sys
from functions.connections import Multicontext
from functions.load_config import load_inventory, load_mail_config
from functions.send_mail import send_mail
from functions.find_delta import create_diff_files
from functions.check_role import check_role
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


def get_inventory(inv):
    """ """
    # TODO
    devices = []
    for device in inv.devices:
        # active = Multicontext(
        #     name=inv.devices["fw_a"].get("name"),
        #     host=inv.devices["fw_a"]["connection"]["host"],
        #     username=inv.devices["fw_a"]["connection"]["username"],
        #     device_type=inv.devices["fw_a"]["connection"]["device_type"],
        #     enable_required=inv.devices["fw_a"]["connection"]["enable_required"],
        # )
        devices.append(
            Multicontext(
                name=inv.devices[device].get("name"),
                host=inv.devices[device]["connection"]["host"],
                username=inv.devices[device]["connection"]["username"],
                device_type=inv.devices[device]["connection"]["device_type"],
                fast_cli=inv.devices[device]["connection"]["fast_cli"],
                enable_required=inv.devices[device]["connection"]["enable_required"],
            )
        )

    return devices


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
    attached_files = [logfile]

    inv_path = os.path.join(app_config_path, "inventory", args.filename)
    inv = load_inventory(inv_path)

    devices = get_inventory(inv)

    for fw in devices:
        fw.check_reachability()
        if not fw.is_reachable:
            msg = f"Не удалось подключиться к {fw.name}"
            send_mail(msg, files=[logfile], **mail_config.dict())
            sys.exit(msg)

    for fw in devices:
        fw.get_contexts()
    #     for context in fw.contexts:
    #         fw.is_active = check_role(context)  # if it's active site sets fw.is_active = True  else False

    for fw in devices:
        for context in fw.contexts:
            fw.get_context_backup(context)
            fw.save_backup_to_file(context, datetime_now)

    active_fw, standby_fw = check_role(environment, app_config, devices)

    active_fw, standby_fw, attached_files = create_diff_files(
        attached_files, active_fw, standby_fw, datetime_now
    )

    send_mail(f"Active FW - {active_fw.name} <br>Standby FW - {standby_fw.name}", files=attached_files, **mail_config.dict())
    pass


if __name__ == "__main__":
    main()
