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


reserve_delta = """!
object-group protocol res_only
 description test_og_prot
!
object-group protocol obj_prot0
 description test_og_prot
 protocol-object udp
!""".splitlines()

def test_intersection_of_equal_lists():
    assert not intersection(active_delta, active_delta)



def test_intersection():
    assert intersection(active_delta, reserve_delta)

def test_intersection_check_only():
    assert 'object-group protocol act_only' not in intersection(active_delta, reserve_delta)
    assert 'object-group protocol res_only' not in intersection(active_delta, reserve_delta)

def test_intersection2():
    assert intersection(active_delta, reserve_delta) == ['object-group protocol obj_prot0', ' protocol-object icmp', ' no protocol-object udp']


def test_get_acl():
    config = """!
access-list test extended permit ip any any time-range tr1 
access-list test extended permit ip any any time-range tr49 
access-list acl_og0 extended deny ip object-group og0 host 8.8.8.8 
access-list acl_og1 extended deny ip object-group og1 host 8.8.8.8 
access-list acl_og2 extended deny ip object-group og2 host 8.8.8.8 
access-list acl_og3 extended deny ip object-group og3 host 8.8.8.8 
!""".splitlines()


    test_acl = get_acl(config).get('test')
    assert test_acl == ['access-list test extended permit ip any any time-range tr1 ', 'access-list test extended permit ip any any time-range tr49 ']
    assert get_acl(config).get('acl_og1') == ['access-list acl_og1 extended deny ip object-group og1 host 8.8.8.8 ']


    commands = create_acl(config, ['access-list test extended permit ip any any time-range tr1 '])
    assert commands == ['clear configure access-list test', 'access-list test extended permit ip any any time-range tr1 ', 'access-list test extended permit ip any any time-range tr49 ']

    commands = create_acl(config, ['access-list test extended permit ip any any time-range tr1', 'access-list acl_og0 extended deny ip object-group og2 host 8.8.8.83'])
    assert 'clear configure access-list test' in commands
    assert 'clear configure access-list acl_og0' in commands
    # print(commands)
    assert commands == ['clear configure access-list test', 'access-list test extended permit ip any any time-range tr1 ', 'access-list test extended permit ip any any time-range tr49 ', 'clear configure access-list acl_og0', 'access-list acl_og0 extended deny ip object-group og0 host 8.8.8.8 ']

def test_intersection3():
    active = """!
object-group network og10
 network-object host 1.1.1.1
 network-object host 1.1.1.2
 network-object host 1.1.1.3
 network-object host 1.1.1.4
 network-object 10.1.1.0 255.255.255.0""".splitlines()

    reserve = """!
object-group network og10
 network-object host 1.1.1.1
 network-object 10.1.1.0 255.255.255.0""".splitlines()

    commands = intersection(active, reserve)
    assert commands == ['object-group network og10', ' network-object host 1.1.1.2', ' network-object host 1.1.1.3', ' network-object host 1.1.1.4']

def test_intersection4():

    active = """!
object-group network og0
 network-object host 1.1.1.111
 network-object host 1.1.1.3
 """.splitlines()

    reserve = """!
object-group network og0
 network-object host 1.1.1.1
 network-object host 1.1.1.2
 network-object host 1.1.1.3
 network-object host 1.1.1.4
 network-object 10.1.1.0 255.255.255.0
 """.splitlines()


    commands = intersection(active, reserve)
    # print(commands)
    assert commands == ['object-group network og0', ' network-object host 1.1.1.111', ' no network-object host 1.1.1.1', ' no network-object host 1.1.1.2', ' no network-object host 1.1.1.4', ' no network-object 10.1.1.0 255.255.255.0']

