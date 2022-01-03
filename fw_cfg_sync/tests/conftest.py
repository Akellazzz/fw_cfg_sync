from ..functions.load_config import load_config
import os
from .abs_path import dirname
import pytest


def pytest_configure(config):
    """
    Register the `focus` marker, so we don't get warnings.
    """

    config.addinivalue_line("markers", "focus: Only run this test.")

    inv = load_config(os.path.join(dirname, "inventory", "dev_config.yaml"))
    for device in inv.devices:
        if inv.devices[device]["role"] == "active":
            active = inv.devices[device]["name"]
            pytest.active_conn = inv.devices[device]["connection"]
        elif inv.devices[device]["role"] == "standby":
            standby = inv.devices[device]["name"]
            pytest.standby_conn = inv.devices[device]["connection"]
        elif inv.devices[device]["role"] == "switch":
            switch = inv.devices[device]["name"]
            pytest.switch_conn = inv.devices[device]["connection"]
    pytest.fw_configs = {
        "active_backup": os.path.join(dirname, "fw_configs", f"{active}.txt"),
        "standby_old_backup": os.path.join(dirname, "fw_configs", f"{standby}_old.txt"),
        "standby_commands": os.path.join(
            dirname, "fw_configs", f"{standby}_commands.txt"
        ),
        "standby_new_backup": os.path.join(dirname, "fw_configs", f"{standby}_new.txt"),
    }
