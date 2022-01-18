from ...functions.load_config import *
from ..abs_path import *


def test_load_config():

    file = path_to_test_inventory + "datamodel.yaml"
    with open(file, "r") as stream:
        try:
            init_config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    assert Prerequisites(**init_config["prerequisites"])
    assert Connection(**init_config["devices"]["fw_a"]["connection"])
    assert Device(**init_config["devices"]["fw_a"])
    assert Device(**init_config["devices"]["fw_b"])
    assert Devices(devices=init_config["devices"])
    assert load_config(file)
