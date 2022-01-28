from ciscoconfparse import CiscoConfParse
from ...functions.find_delta import block_parser, find_delta
import os
import pytest

def test_block_parser():
    with open(os.path.join(pytest.tests_dir, 'fw_configs_for_tests', "active_cfg_file.txt")) as f:
        parse = CiscoConfParse(f.readlines())

    x = block_parser(parse, r"^policy-map\s")
    assert "policy-map" in x[0].ioscfg[0]

def test_find_delta():

    file1 = os.path.join(pytest.tests_dir, 'fw_configs_for_tests', "active_cfg_file.txt")
    file2 = os.path.join(pytest.tests_dir, 'fw_configs_for_tests', "active_cfg_file.txt")

    file1_uniq, file2_uniq = find_delta(
        "active",
        file1,
        "standby",
        file2
    )
    assert file1_uniq == file2_uniq
    # pass                    