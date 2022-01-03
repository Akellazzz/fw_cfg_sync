import sys

from ..abs_path import *
from ...functions.helpers import config_parser_sum

from ciscoconfparse import CiscoConfParse


def test_config_parser_sum():

    result1 = config_parser_sum(active_cfg_file)
    result2 = config_parser_sum(active_cfg_file)
    assert len(result1) > 0 and len(result2) > 0

    assert isinstance(result1, list)
    assert isinstance(result2, list)
    assert result1 == result2
