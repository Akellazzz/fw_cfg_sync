from ciscoconfparse import CiscoConfParse
import os
import sys
import pytest
from pprint import pprint
from pathlib import Path

sys.path.insert(0, str(Path(__file__) / ".." / ".." / ".."))
sys.path.insert(0, str(Path(__file__) / ".." / ".." / ".." / "functions"))
# print(str(Path(__file__) / ".." / ".." / ".." / "functions"))
# from ...functions.create_commands import intersection, get_acl, create_acl, create_commands, acls_to_be_removed, acls_to_be_created, create_acl_changes
from functions.create_commands import _intersection, create_commands

active = """object-group protocol obj_prot0
 description test_og_prot
 protocol-object icmp
!
object-group protocol act_only
 description test_og_prot
""".splitlines()

active_delta = """object-group protocol obj_prot0
 description test_og_prot
 protocol-object icmp
!
object-group protocol act_only
 description test_og_prot
""".splitlines()

reserve = """object-group protocol res_only
 description test_og_prot
!
object-group protocol obj_prot0
 description test_og_prot
 protocol-object udp
""".splitlines()

reserve_delta = """object-group protocol res_only
 description test_og_prot
!
object-group protocol obj_prot0
 description test_og_prot
 protocol-object udp
""".splitlines()


def test_intersection_of_equal_lists():

    assert not _intersection(active, active, [], [])


def test_intersection():
    assert _intersection(active, reserve, active_delta, reserve_delta)


def test_intersection_check_only():
    assert "object-group protocol act_only" not in _intersection(
        active, reserve, active_delta, reserve_delta
    )
    assert "object-group protocol res_only" not in _intersection(
        active, reserve, active_delta, reserve_delta
    )


def test_intersection2():
    result = _intersection(active, reserve, active_delta, reserve_delta)
    # print(result)
    # breakpoint()
    # assert  == ['object-group protocol obj_prot0', ' protocol-object icmp', ' no protocol-object udp']


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

    active_delta = """!
object-group network og10
 network-object host 1.1.1.1
 network-object host 1.1.1.2
 network-object host 1.1.1.3
 network-object host 1.1.1.4
 network-object 10.1.1.0 255.255.255.0""".splitlines()

    reserve_delta = """!
object-group network og10
 network-object host 1.1.1.1
 network-object 10.1.1.0 255.255.255.0""".splitlines()

    commands = _intersection(active, reserve, active_delta, reserve_delta)
    # print(commands)

    assert commands == [
        "object-group network og10",
        " network-object host 1.1.1.2",
        " network-object host 1.1.1.3",
        " network-object host 1.1.1.4",
    ]


def test_create_commands():
    act_backup = """!
access-list both_with_diff extended permit ip any any time-range tr0
access-list both_with_diff extended permit ip any any time-range act_diffffffff
access-list both_with_diff extended permit ip any any time-range tr2
access-list act_only extended deny ip object-group og0 host 8.8.8.8
access-list act_only extended deny ip object-group og1 host 8.8.8.8
!
object-group protocol obj_prot0
 description test_og_prot
 protocol-object icmp
!
object-group protocol act_only
 description test_og_prot
!""".splitlines()

    res_backup = """!
access-list both_with_diff extended permit ip any any time-range tr0
access-list both_with_diff extended permit ip any any time-range act_diffffffff
access-list both_with_diff extended permit ip any any time-range tr2
access-list res_only extended deny ip object-group og2 host 8.8.8.8
object-group network res_only
 network-object 10.1.1.0 255.255.255.0
!""".splitlines()

    active_delta = """!
access-list both_with_diff extended permit ip any any time-range act_diffffffff
access-list act_only extended deny ip object-group og0 host 8.8.8.8
access-list act_only extended deny ip object-group og1 host 8.8.8.8
!
object-group protocol act_only
 description test_og_prot
""".splitlines()

    reserve_delta = """!
access-list both_with_diff extended permit ip any any time-range res_diffffffff
access-list res_only extended deny ip object-group og2 host 8.8.8.8
object-group network res_only
 network-object 10.1.1.0 255.255.255.0
""".splitlines()

    commands = create_commands(act_backup, res_backup, active_delta, reserve_delta)
    assert " both " not in commands
    for line in commands:
        if "res_only" in line:
            assert line.strip().startswith("no ")
    # print('\n'.join(commands))


def test_create_commands2():

    active_config = """!
""".splitlines()

    reserve_config = """!
access-list test extended permit ip host host2 any
""".splitlines()

    active_delta = "".splitlines()

    reserve_delta = """!
access-list test extended permit ip host host2 any
""".splitlines()

    commands = create_commands(
        active_config, reserve_config, active_delta, reserve_delta
    )
    pprint(commands)
    assert commands == ["no access-list test extended permit ip host host2 any"]
    # print('\n'.join(commands))
