from ...functions.load_config import Prerequisites, load_inventory
from ...functions.connections import Multicontext
import pytest
import os
import yaml


def test_load_config():

    file = os.path.join(pytest.tests_dir, "datamodel.yaml")
    with open(file, "r") as stream:
        try:
            init_config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    assert Prerequisites(**init_config["prerequisites"])
    assert load_inventory(file)


def test_Multicontext():
    inv_path = os.path.join(pytest.tests_dir, "datamodel.yaml")
    inv = load_inventory(inv_path)

    devices = []
    for device in inv.devices:
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

    assert isinstance(devices[0], Multicontext)
