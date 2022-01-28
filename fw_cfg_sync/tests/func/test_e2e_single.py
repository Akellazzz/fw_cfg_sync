import sys
import os
import pytest
from ciscoconfparse import CiscoConfParse

from ..abs_path import *
from ...functions.backup_cfg import save_run_cfg_locally
from ...functions.create_cfg_for_standby import create_cfg_for_standby
from ...functions.deploy_cfg_to_standby import deploy_cfg_to_standby
from ...functions.deploy_cfg_to_standby import clear_config
from ...functions.old.compare_cfg import compare_cfg
from ...functions.helpers import init_config
from ...functions.helpers import PARSE_DICT, config_parser, erase_file
from ...functions.connection import send_config_from_file


# @pytest.fixture()
# def ():
#     inv = load_config(os.path.join(dirname, "inventory", "dev_config.yaml"))
#     for device in inv.devices:
#         if inv.devices[device]["role"] == "active":
#             active = inv.devices[device]["name"]
#             pytest.active_conn = inv.devices[device]["connection"]
#         elif inv.devices[device]["role"] == "standby":
#             standby = inv.devices[device]["name"]
#             pytest.standby_conn = inv.devices[device]["connection"]
#         elif inv.devices[device]["role"] == "switch":
#             switch = inv.devices[device]["name"]
#             switch_conn = inv.devices[device]["connection"]
#     pytest.fw_configs = {
#         "active_backup": os.path.join(dirname, "pytest.fw_configs", f"{active}.txt"),
#         "standby_old_backup": os.path.join(dirname, "pytest.fw_configs", f"{standby}_old.txt"),
#         "standby_commands": os.path.join(
#             dirname, "pytest.fw_configs", f"{standby}_commands.txt"
#         ),
#         "standby_new_backup": os.path.join(dirname, "pytest.fw_configs", f"{standby}_new.txt"),
#     }
#     return pytest.active_conn, pytest.standby_conn, pytest.fw_configs


def keys_in_config(config):
    with open(config, "r") as f:
        parse = CiscoConfParse(f.readlines())
    for template in PARSE_DICT.values():
        if "names" in template:
            continue
        if not bool(config_parser(parse, template)):
            return False
    return True


def test_erase_files():
    for file in pytest.fw_configs.values():
        erase_file(file)
        assert os.stat(file).st_size == 0


# @pytest.mark.skip()
def test_clear_active_cfg():
    clear_config(pytest.active_conn, clear_config_test_commands)


# @pytest.mark.skip()
# @pytest.mark.connection()
def test_configure_active():
    # Отправляет фейковый сгенерированный конфиг на активный МСЭ

    result = send_config_from_file(pytest.active_conn, fake_config_short)

    if result.failed:
        print("Unable to configure FW")
        sys.exit()


# @pytest.mark.connection()
def test_backup_cfg():
    save_run_cfg_locally(pytest.active_conn, pytest.fw_configs["active_backup"])
    save_run_cfg_locally(pytest.standby_conn, pytest.fw_configs["standby_old_backup"])


def test_fw_cfg_files_exist():
    # Проверяет, что созданы бэкапы МСЭ

    with open(pytest.fw_configs["active_backup"], "r") as f:
        x = f.read()
        assert x.endswith("end")

    with open(pytest.fw_configs["standby_old_backup"], "r") as f:
        x = f.read()
        assert x.endswith("end")


def test_keys_in_active_cfg_file_backup():
    # Проверяет, что в бэкапе активного МСЭ есть синхронизируемые блоки конфига
    assert keys_in_config(pytest.fw_configs["active_backup"])


def test_create_cfg_for_standby():
    create_cfg_for_standby(
        pytest.fw_configs["active_backup"], pytest.fw_configs["standby_commands"]
    )


def test_cfg_for_standby_exist():
    # Проверяет, что создан конфиг для standby

    with open(pytest.fw_configs["standby_commands"], "r") as f:
        x = f.read()
        assert "time-range " in x


def test_deploy_cfg_to_standby():
    deploy_cfg_to_standby(
        pytest.standby_conn,
        pytest.fw_configs["standby_commands"],
        pytest.fw_configs["standby_new_backup"],
        clear_config_test_commands,
    )


def test_new_standby_test_cfg_exist():
    # Проверяет, что создан новый бэкап для standby

    with open(pytest.fw_configs["standby_new_backup"], "r") as f:
        x = f.read()
        assert x.endswith("end")


def test_compare_cfg():
    assert compare_cfg(
        pytest.fw_configs["active_backup"], pytest.fw_configs["standby_new_backup"]
    )
