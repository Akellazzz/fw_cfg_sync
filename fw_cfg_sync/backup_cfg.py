from datetime import datetime
from functions.load_config import load_config
from functions.backup_cfg import save_run_cfg_locally
from argparse import ArgumentParser, RawTextHelpFormatter
import os


def getargs():
    parser = ArgumentParser(
        description=f"""Сохраняет бэкап в директорию fw_configs
Пример: py backup_cfg.py -f dev_config.yaml -n asa1""",
        formatter_class=RawTextHelpFormatter,
    )  # TODO
    parser.add_argument(
        "-f",
        dest="filename",
        type=str,
        help="инвентарный файл из каталога inventory",
        required=True,
    )
    parser.add_argument(
        "-n", dest="name", type=str, help=f"имя устройства", required=True
    )
    return parser.parse_args()


def main():
    d = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    args = getargs()
    dirname = os.path.dirname(__file__)
    p = os.path.join(dirname, "inventory", args.filename)
    inv = load_config(p)
    for device in inv.devices:
        if inv.devices.get(device).get("name") == args.name:
            print(f"Found {args.name}")
            conn = inv.devices.get(device).get("connection")
            filename = os.path.join(dirname, "fw_configs", f"{args.name}_{d}.txt")

    save_run_cfg_locally(conn, filename)


# py backup_cfg.py -f dev_config.yaml -n asa1

if __name__ == "__main__":
    main()
