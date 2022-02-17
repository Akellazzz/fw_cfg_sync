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
    parser.add_argument(
        "-act",
        dest="act_backup",
        type=str,
        help="бэкап активного контекста",
        required=True,
    )
    return parser.parse_args()


def main():
    args = getargs()
    if args:
        if args.verbose:
            logger.add(sys.stdout, level="DEBUG")
    else:
        logger.add(sys.stdout, format="{message}", level="INFO")

    file1 = args.file1
    file2 = args.file2
    act_backup = args.act_backup
    uniq_in_file1, uniq_in_file2 = find_delta(file1, file2)

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
    if uniq_in_file1 or uniq_in_file2:
        print(f"Если file1 брать за эталон, то для file2 команды:")

        pprint(create_commands(act_backup.splitlines(), uniq_in_file1.splitlines(), uniq_in_file2.splitlines()))

if __name__ == "__main__":
    main()
