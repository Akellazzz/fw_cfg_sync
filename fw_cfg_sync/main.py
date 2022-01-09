import os
import sys
import pickle
from functions.connections import Multicontext
from functions.load_config import load_config
from argparse import ArgumentParser, RawTextHelpFormatter

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
        help="Уровень логирования DEBUG (по умолчанию INFO)",
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


def set_roles(inv):
    # TODO
    active = Multicontext(
        name=inv.devices["fw_a"].get("name"),
        host=inv.devices["fw_a"]["connection"]["host"],
        username=inv.devices["fw_a"]["connection"]["username"],
        device_type=inv.devices["fw_a"]["connection"]["device_type"],
        enable_required=inv.devices["fw_a"]["connection"]["enable_required"],
    )
    standby = Multicontext(
        name=inv.devices["fw_b"].get("name"),
        host=inv.devices["fw_b"]["connection"]["host"],
        username=inv.devices["fw_b"]["connection"]["username"],
        device_type=inv.devices["fw_b"]["connection"]["device_type"],
        enable_required=inv.devices["fw_b"]["connection"]["enable_required"],
    )

    return active, standby


def main():
    args = getargs()

    main_dir = os.path.dirname(sys.argv[0])  # путь к главной директории
    logs_dir = os.path.join(main_dir, "logs")

    log_config = {
        "handlers": [
            {
                "sink": f"{logs_dir}" + "/fw_cfg_sync_{time}.log",
                "retention": "30 days",
                "backtrace": True,
                "diagnose": True,
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

    p = os.path.join(main_dir, "inventory", args.filename)
    inv = load_config(p)
    active, standby = set_roles(inv)
    for device in active, standby:
        device.check_reachability()
        if not device.is_reachable:
            pass
            # mail() #TODO
            sys.exit(f"Не удалось подключиться к {device.name}")

    active.get_contexts()
    for context in active.contexts:
        active.get_context_backup(context)
        active.save_backup_to_file(context)

    # with open("fw_cfg_sync\\tests\\fw_configs\\pickle_dumps\\active_with_backups2.pickle", 'wb') as f:
    #     pickle.dump(active, f)
    # with open("fw_cfg_sync\\tests\\fw_configs\\pickle_dumps\\standby_unreacheble.pickle", 'wb') as f:
    #     pickle.dump(standby, f)

    # with open("fw_cfg_sync\\tests\\fw_configs\\pickle_dumps\\active_with_backups2.pickle", 'rb') as f:
    #     active = pickle.load(f)
    # with open("fw_cfg_sync\\tests\\fw_configs\\pickle_dumps\\standby_unreacheble.pickle", 'rb') as f:
    #     standby = pickle.load(f)

    # keyring.set_password("fw1", "aaa", "aaa")
    # p = keyring.get_password("fw1", "aaa")
    # print(p)
    pass


if __name__ == "__main__":
    main()
