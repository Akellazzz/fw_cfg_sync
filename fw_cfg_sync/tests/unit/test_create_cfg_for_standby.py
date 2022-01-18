import os
from ..abs_path import *
from ...functions.helpers import erase_file
from ...functions.create_cfg_for_standby import create_cfg_for_standby


def test_create_cfg_for_standby():

    erase_file(config_for_standby_test_file)
    assert os.stat(config_for_standby_test_file).st_size == 0

    create_cfg_for_standby(active_cfg_file_backup, config_for_standby_test_file)
    with open(config_for_standby_test_file, "r") as f:
        x = f.read()
        assert "class-map" in x
