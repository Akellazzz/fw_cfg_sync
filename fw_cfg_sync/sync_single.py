from sys import exit
from sys import argv
from functions.load_config import load_config
from functions.helpers import PARSE_DICT, config_parser, erase_file
from functions.backup_cfg import save_run_cfg_locally
from functions.create_cfg_for_standby import create_cfg_for_standby
from functions.compare_cfg import compare_cfg
from functions.deploy_cfg_to_standby import deploy_cfg_to_standby

from argparse import ArgumentParser, RawTextHelpFormatter
import os


def getargs():
    modes = ["sync", "check"]
    reports = ["cli", "mail"]
    parser = ArgumentParser(
        description=f"""Программа синхронизации конфигураций МСЭ между площадками.
Документация - wiki""",
        formatter_class=RawTextHelpFormatter,
    )  # TODO
    parser.add_argument(
        "-f",
        dest="filename",
        type=str,
        help="инвентарный файл из каталога inventory",
        required=True,
    )
    parser.add_argument("-m", dest="mode", type=str, help=f"{modes}", required=True)
    parser.add_argument("-r", dest="report", type=str, help=f"{reports}", required=True)
    return parser.parse_args()


def main():
    args = getargs()
    dirname = os.path.dirname(__file__)
    p = os.path.join(dirname, "inventory", args.filename)
    inv = load_config(p)
    # print(args.mode)
    # print(args.report)
    # print(inv.prerequisites)
    for device in inv.devices:
        if inv.devices[device]["role"] == "active":
            active = inv.devices[device]["name"]
            active_conn = inv.devices[device]["connection"]
        elif inv.devices[device]["role"] == "standby":
            standby = inv.devices[device]["name"]
            standby_conn = inv.devices[device]["connection"]
        elif inv.devices[device]["role"] == "switch":
            switch = inv.devices[device]["name"]
            switch_conn = inv.devices[device]["connection"]
    fw_configs = {
        "active_backup": os.path.join(dirname, "fw_configs", f"{active}.txt"),
        "standby_old_backup": os.path.join(dirname, "fw_configs", f"{standby}_old.txt"),
        "standby_commands": os.path.join(
            dirname, "fw_configs", f"{standby}_commands.txt"
        ),
        "standby_new_backup": os.path.join(dirname, "fw_configs", f"{standby}_new.txt"),
    }
    for file in fw_configs.values():
        erase_file(file)

    save_run_cfg_locally(active_conn, fw_configs["active_backup"])
    save_run_cfg_locally(standby_conn, fw_configs["standby_old_backup"])

    create_cfg_for_standby(fw_configs["active_backup"], fw_configs["standby_commands"])

    # TODO
    deploy_cfg_to_standby(
        standby_conn,
        fw_configs["standby_commands"],
        fw_configs["standby_new_backup"],
        "C:\\Users\\eekosyanenko\\Documents\\poetry-fw_cfg_sync\\poetry_fw_cfg_sync\\tests\\fw_configs_for_tests\\clear_config_test_commands.txt"
    )

    assert compare_cfg(fw_configs["active_backup"], fw_configs["standby_new_backup"])

# py sync_single.py -f dev_config.yaml -m check -r cli

if __name__ == "__main__":
    main()
