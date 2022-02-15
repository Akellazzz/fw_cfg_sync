from ciscoconfparse import CiscoConfParse
import os
import sys
import pytest
from pprint import pprint
from pathlib import Path
sys.path.insert(0, str(Path(__file__) / ".." / ".." / ".." / "functions"))
# print(str(Path(__file__) / ".." / ".." / ".." / "functions"))
from ...functions.create_commands import intersection


active_delta = """!
object-group protocol obj_prot0
 description test_og_prot
 protocol-object icmp
!
object-group protocol act_only
 description test_og_prot
!""".splitlines()

def test_intersection_of_equal_lists():
    assert not intersection(active_delta, active_delta)

reserve_delta = """!
object-group protocol res_only
 description test_og_prot
!
object-group protocol obj_prot0
 description test_og_prot
 protocol-object udp
!""".splitlines()


def test_intersection():
    assert intersection(active_delta, reserve_delta)

def test_intersection_check_only():
    assert 'object-group protocol act_only' not in intersection(active_delta, reserve_delta)
    assert 'object-group protocol res_only' not in intersection(active_delta, reserve_delta)

def test_intersection2():
    assert intersection(active_delta, reserve_delta) == ['object-group protocol obj_prot0', ' no protocol-object udp', ' protocol-object icmp', '!']

def test_intersection3():
    print(intersection(active_delta, reserve_delta))
    assert intersection(active_delta, reserve_delta) == ['object-group protocol obj_prot0', ' no protocol-object udp', ' protocol-object icmp', '!']

