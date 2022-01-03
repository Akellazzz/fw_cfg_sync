from ..abs_path import *
from ciscoconfparse import CiscoConfParse
from ...functions.helpers import config_parser


def test_config_parser():

    with open(active_cfg_file, "r") as f:
        parse = CiscoConfParse(f.readlines())

    x = config_parser(parse, r"^policy-map\s")
    assert "policy-map" in x[0].ioscfg[0]
