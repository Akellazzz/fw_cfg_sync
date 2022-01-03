from ..abs_path import *
from ...functions.helpers import config_parser_sum
import pytest


def test_compare_cfg():
    assert config_parser_sum(active_cfg_file) != config_parser_sum(
        changed_active_cfg_file
    )
