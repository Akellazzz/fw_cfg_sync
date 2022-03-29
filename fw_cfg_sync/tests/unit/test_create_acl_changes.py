from ciscoconfparse import CiscoConfParse
import os
import sys
import pytest
from pprint import pprint
from pathlib import Path
sys.path.insert(0, str(Path(__file__) / ".." / ".." / ".."))
# print(str(Path(__file__) / ".." / ".." / ".." / "functions"))
from functions.create_commands import create_acl_changes, get_acl, acls_to_be_removed

def test_create_acl_changes1():
    # когда в ACL одна строка и она отличается, нужно сначала добавить вторую, а потом удалить первую

    active_config = """!
access-list both extended permit ip any any time-range both
access-list both_with_diff extended permit ip any any time-range act_diffffffff
access-list act_only extended deny ip object-group og0 host 8.8.8.8
access-list act_only extended deny ip object-group og1 host 8.8.8.8
!
object-group protocol act_only
 description test_og_prot
""".splitlines()

    reserve_config = """!
access-list both extended permit ip any any time-range both
access-list both_with_diff extended permit ip any any time-range res_diffffffff
access-list res_only extended deny ip object-group og2 host 8.8.8.8
object-group network res_only
 network-object 10.1.1.0 255.255.255.0
""".splitlines()

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

    commands = create_acl_changes(active_config, reserve_config, active_delta, reserve_delta)
    pprint(commands)
    assert commands == ['access-list both_with_diff deny icmp host 1.1.1.1 host 1.1.1.1', 'no access-list both_with_diff extended permit ip any any time-range res_diffffffff', 'access-list both_with_diff extended permit ip any any time-range act_diffffffff', 'no access-list both_with_diff deny icmp host 1.1.1.1 host 1.1.1.1']
    # print('\n'.join(commands))



def test_create_acl_changes2():
    # в резервном есть все из активного в правильном порядке и есть лишние. Только они должны быть удалены.

    active_config = """!
access-list both extended permit ip any any time-range a
access-list both extended permit ip any any time-range b
access-list both extended permit ip any any time-range c
""".splitlines()

    reserve_config = """!
access-list both extended permit ip any any time-range a
access-list both extended permit ip any any time-range b
access-list both extended permit ip any any time-range c
access-list both extended permit ip any any time-range d
access-list both extended permit ip any any time-range e
""".splitlines()

    active_delta = []

    reserve_delta = """!
access-list both extended permit ip any any time-range d
access-list both extended permit ip any any time-range e
""".splitlines()

    commands = create_acl_changes(active_config, reserve_config, active_delta, reserve_delta)
    assert commands == ['no access-list both extended permit ip any any time-range d', 'no access-list both extended permit ip any any time-range e']
    # print('\n'.join(commands))



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



