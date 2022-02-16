from ciscoconfparse import CiscoConfParse
import os
import sys
import pytest
from pprint import pprint
from pathlib import Path
sys.path.insert(0, str(Path(__file__) / ".." / ".." / ".." / "functions"))
# print(str(Path(__file__) / ".." / ".." / ".." / "functions"))
from ...functions.create_commands import intersection, get_acl, create_acl


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
    # print(intersection(active_delta, reserve_delta))
    assert intersection(active_delta, reserve_delta) == ['object-group protocol obj_prot0', ' no protocol-object udp', ' protocol-object icmp', '!']

config = """!
access-list test extended permit ip any any time-range tr1 
access-list test extended permit ip any any time-range tr49 
access-list acl_og0 extended deny ip object-group og0 host 8.8.8.8 
access-list acl_og1 extended deny ip object-group og1 host 8.8.8.8 
access-list acl_og2 extended deny ip object-group og2 host 8.8.8.8 
access-list acl_og3 extended deny ip object-group og3 host 8.8.8.8 
!""".splitlines()


def test_get_acl():
    test_acl = get_acl(config).get('test')
    assert test_acl == ['access-list test extended permit ip any any time-range tr1 ', 'access-list test extended permit ip any any time-range tr49 ']
    assert get_acl(config).get('acl_og1') == ['access-list acl_og1 extended deny ip object-group og1 host 8.8.8.8 ']


def test_create_acl():
    commands = create_acl(config, ['access-list test extended permit ip any any time-range tr1 '])
    assert commands == ['clear configure access-list test', 'access-list test extended permit ip any any time-range tr1 ', 'access-list test extended permit ip any any time-range tr49 ']


config2 = """access-list test extended permit ip any any time-range tr1
access-list test extended permit ip any any time-range tr49
access-list acl_og0 extended deny ip object-group og0 host 8.8.8.81
access-list acl_og0 extended deny ip object-group og1 host 8.8.8.82
access-list acl_og0 extended deny ip object-group og2 host 8.8.8.83
access-list acl_og0 extended deny ip object-group og3 host 8.8.8.84
""".splitlines()

def test_create_acl2():
    commands = create_acl(config, ['access-list test extended permit ip any any time-range tr1', 'access-list acl_og0 extended deny ip object-group og2 host 8.8.8.83'])
    assert 'clear configure access-list test' in commands
    assert 'clear configure access-list acl_og0' in commands
    # print(commands)
    assert commands == ['clear configure access-list test', 'access-list test extended permit ip any any time-range tr1 ', 'access-list test extended permit ip any any time-range tr49 ', 'clear configure access-list acl_og0', 'access-list acl_og0 extended deny ip object-group og0 host 8.8.8.8 ']

