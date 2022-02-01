""" Сравнение двух конфигураций Cisco ASA

Пример: 

find_diff.py -i -f1 tests\fw_configs_for_tests\active_cfg_file.txt -f2 tests\fw_configs_for_tests\active_cfg_file_changed.txt
"""

import time
from argparse import ArgumentParser, RawTextHelpFormatter

from functions.find_delta import find_delta
from functions.find_delta import block_parser
from functions.find_delta import get_uniq
import sys
import yaml
import os
from loguru import logger
from ciscoconfparse import CiscoConfParse


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
        "-i",
        "--ignore_empty_timeranges",
        help="Не выводить дельту для acl с пустыми time-range",
        action="store_true",
    )

    parser.add_argument(
        "-f1",
        dest="file1",
        type=str,
        help="файл с конфигурацией для сравнения",
        required=True,
    )
    parser.add_argument(
        "-f2",
        dest="file2",
        type=str,
        help="файл с конфигурацией для сравнения",
        required=True,
    )
    return parser.parse_args()


def get_parser_config():
    app_config_path = os.environ.get("FW-CFG-SYNC_APP_CONFIG")
    config_file = os.path.join(app_config_path, "parser_config.yaml")
    # logger.debug(f"Конфигурация парсера: {config_file} ")

    with open(config_file) as f:
        parser_config = yaml.safe_load(f)
    return parser_config


def cut_empty_tr(acl_list, empty_tr):
    acl_with_cutted_empty_tr = []
    for i in acl_list:
        tr = ""
        if " time-range " in i:
            acl_wo_tr = i.split(" time-range ")[0].strip()
            tr = i.split(" time-range ")[-1].strip()
            if tr in empty_tr:
                acl_with_cutted_empty_tr.append(acl_wo_tr)
            else:
                acl_with_cutted_empty_tr.append(i)
        else:
            acl_with_cutted_empty_tr.append(i)
    return acl_with_cutted_empty_tr


def get_tr_in_use(acl: list) -> list:
    return [i.split(" time-range ")[-1].strip() for i in acl if " time-range " in i]


def analize_tr(items):
    empty_tr = []
    not_empty_tr = []
    for i in items:
        if len(i) == 1:
            empty_tr.append(i[0].split()[-1])
        else:
            not_empty_tr.append(i[0].split()[-1])
    return empty_tr, not_empty_tr


def without_empty_tr(file1, file2):

    with open(file1, "r") as f1, open(file2, "r") as f2:
        parse1 = CiscoConfParse(f1.readlines())
        parse2 = CiscoConfParse(f2.readlines())

    parser_config = get_parser_config()

    ### time-range
    ###
    template = parser_config["time-range"].get("template")
    res_original_tr1 = [tuple(i.ioscfg) for i in block_parser(parse1, template)]
    res_original_tr2 = [tuple(i.ioscfg) for i in block_parser(parse2, template)]

    empty_tr_1, not_empty_tr_1 = analize_tr(res_original_tr1)
    empty_tr_2, not_empty_tr_2 = analize_tr(res_original_tr2)
    assert bool(set(empty_tr_1) & set(not_empty_tr_1)) == False
    assert bool(set(empty_tr_2) & set(not_empty_tr_2)) == False

    ### acl
    ###
    template = parser_config["access-list"].get("template")
    res_original_acl1 = [tuple(i.ioscfg) for i in block_parser(parse1, template)]
    res_original_acl2 = [tuple(i.ioscfg) for i in block_parser(parse2, template)]

    missed_acl = []
    acl_only_in_1 = []
    acl_only_in_2 = []

    acl_list1 = [x[0].strip() for x in res_original_acl1]
    acl_list2 = [x[0].strip() for x in res_original_acl2]

    acl_with_cutted_empty_tr_1 = cut_empty_tr(acl_list1, empty_tr_1)
    acl_with_cutted_empty_tr_2 = cut_empty_tr(acl_list2, empty_tr_2)

    acl_only_in_1 = []
    for i in acl_list1:
        if i in (acl_list2 + acl_with_cutted_empty_tr_2):
            continue
        elif " time-range " in i:

            acl_wo_tr = i.split(" time-range ")[0].strip()
            tr = i.split(" time-range ")[-1].strip()
            if tr in empty_tr_1 and acl_wo_tr in (
                acl_list2 + acl_with_cutted_empty_tr_2
            ):
                continue
            else:
                acl_only_in_1.append(i)
        else:
            acl_only_in_1.append(i)

    for i in acl_list2:
        if i in (acl_list1 + acl_with_cutted_empty_tr_1):
            continue
        elif " time-range " in i:

            acl_wo_tr = i.split(" time-range ")[0].strip()
            tr = i.split(" time-range ")[-1].strip()
            if tr in empty_tr_2 and acl_wo_tr in (
                acl_list1 + acl_with_cutted_empty_tr_1
            ):
                continue
            else:
                acl_only_in_2.append(i)
        else:
            acl_only_in_2.append(i)

    tr_in_use1 = get_tr_in_use(acl_only_in_1)
    tr_in_use2 = get_tr_in_use(acl_only_in_2)

    file1_result = ""
    file2_result = ""
    for block in parser_config:
        uniq_in_file1 = []
        uniq_in_file2 = []

        template = parser_config[block].get("template")
        if block == "time-range":

            uniq_in_file1, uniq_in_file2 = get_uniq(parse1, parse2, template)
            if uniq_in_file1:
                for parent_and_children in uniq_in_file1:
                    parent = parent_and_children[0].strip()  # time-range empty_tr1
                    if parent.split()[-1] in tr_in_use1:  # empty_tr1
                        file1_result += "".join(parent_and_children)

            if uniq_in_file2:
                for parent_and_children in uniq_in_file2:
                    parent = parent_and_children[0].strip()  # time-range empty_tr1
                    if parent.split()[-1] in tr_in_use2:  # empty_tr1
                        file2_result += "".join(parent_and_children)

        elif block == "access-list":
            file1_result += "\n".join(acl_only_in_1)
            file2_result += "\n".join(acl_only_in_2)

        else:
            uniq_in_file1, uniq_in_file2 = get_uniq(parse1, parse2, template)
            if uniq_in_file1:
                file1_out = str()
                for parent_and_children in uniq_in_file1:
                    file1_out += "".join(parent_and_children)
                file1_result += file1_out

            if uniq_in_file2:
                file2_out = str()
                for parent_and_children in uniq_in_file2:
                    file2_out += "".join(parent_and_children)
                file2_result += file2_out

    return file1_result, file2_result


def main():
    args = getargs()
    ignore_empty_timeranges = False
    if args:
        if args.verbose:
            logger.add(sys.stdout, level="DEBUG")
        if args.ignore_empty_timeranges:
            ignore_empty_timeranges = True
    else:
        logger.add(sys.stdout, format="{message}", level="INFO")
    # breakpoint()

    file1 = args.file1
    file2 = args.file2
    if ignore_empty_timeranges:
        uniq_in_file1, uniq_in_file2 = without_empty_tr(file1, file2)
    else:
        uniq_in_file1, uniq_in_file2 = find_delta(file1, file2)

    # time.sleep(1)
    if uniq_in_file1:
        print(f"\nКоманды только в {file1}:\n")
        print(f"{uniq_in_file1}")
    else:
        print(f"В файле {file1} нет уникальных команд")
    if uniq_in_file2:
        print(f"\nКоманды только в {file2}:\n")
        print(f"{uniq_in_file2}")
    else:
        print(f"В файле {file2} нет уникальных команд")


if __name__ == "__main__":
    main()
