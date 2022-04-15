""" Сравнение двух конфигураций Cisco ASA

Пример: 

show_diff_and_commands.py -act tests\fw_configs_for_tests\active_cfg_file.txt -res tests\fw_configs_for_tests\active_cfg_file_changed.txt
"""
from argparse import ArgumentParser, RawTextHelpFormatter
from pprint import pprint

from functions.find_delta import find_delta
from functions.create_commands import create_commands
import sys
from loguru import logger


def getargs():

    parser = ArgumentParser(
        description=f"""Программа проверки согласованности конфигураций МСЭ между площадками.
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
        "-act",
        dest="act_backup",
        type=str,
        help="бэкап активного контекста",
        required=True,
    )
    parser.add_argument(
        "-res",
        dest="res_backup",
        type=str,
        help="бэкап резервного контекста",
        required=True,
    )
    return parser.parse_args()


def show_diff_and_commands(act_backup, res_backup):
    uniq_in_act_backup, uniq_in_res_backup = find_delta(act_backup, res_backup)

    if uniq_in_act_backup:
        print(f"\nКоманды только в {act_backup}:\n")
        print(f"{uniq_in_act_backup}")
    else:
        print(f"В файле {act_backup} нет уникальных команд")
    if uniq_in_res_backup:
        print(f"\nКоманды только в {res_backup}:\n")
        print(f"{uniq_in_res_backup}")
    else:
        print(f"В файле {res_backup} нет уникальных команд")
    if uniq_in_act_backup or uniq_in_res_backup:
        with open(act_backup) as act:
            act_config_list = act.readlines()
            act_config_list = [i.strip() for i in act_config_list]
        with open(res_backup) as res:
            res_config_list = res.readlines()
            res_config_list = [i.strip() for i in res_config_list]
        print(f"Команды для резервного контекста:")
        commands = create_commands(
            act_config_list,
            res_config_list,
            uniq_in_act_backup.splitlines(),
            uniq_in_res_backup.splitlines(),
        )
        pprint(commands)
    return uniq_in_act_backup, uniq_in_res_backup, commands


def main():
    args = getargs()
    if args:
        if args.verbose:
            logger.add(sys.stdout, level="DEBUG")
    else:
        logger.add(sys.stdout, format="{message}", level="INFO")

    act_backup = args.act_backup
    res_backup = args.res_backup
    show_diff_and_commands(act_backup, res_backup)


if __name__ == "__main__":
    main()
