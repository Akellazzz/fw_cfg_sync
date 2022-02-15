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
object-group protocol obj_prot1
 description test_og_prot
 protocol-object icmp
!
access-list act_only extended deny ip object-group og0 host 8.8.8.8 
access-list acl_og0 extended deny ip object-group og0 host 8.8.8.8 
!""".splitlines()

reserve_delta = """!
object-group protocol obj_prot0
 description test_og_prot
 protocol-object udp
!
object-group protocol res_only
 description test_og_prot
 protocol-object udp
!
access-list res_only extended deny ip object-group og0 host 8.8.8.8 
access-list acl_og0 extended deny ip object-group og0 host 8.8.8.8 
!""".splitlines()


def test_intersection_of_equal_lists():
    assert not intersection(active_delta, active_delta)

def test_intersection():
    print('\n')
    print(intersection(active_delta, reserve_delta))
    assert intersection(active_delta, reserve_delta)

