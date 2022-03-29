from ciscoconfparse import CiscoConfParse
import os
import sys
import pytest
from pprint import pprint
from pathlib import Path
sys.path.insert(0, str(Path(__file__) / ".." / ".." / ".." ))
sys.path.insert(0, str(Path(__file__) / ".." / ".." / ".." / "functions"))
# print(str(Path(__file__) / ".." / ".." / ".." / "functions"))
# from ...functions.create_commands import intersection, get_acl, create_acl, create_commands, acls_to_be_removed, acls_to_be_created, create_acl_changes
from functions.create_commands import intersection, create_commands



def test_create_commands2():
    act_backup = """!
class-map inspection_default
 match default-inspection-traffic
!
!
policy-map type inspect dns migrated_dns_map_1
 parameters
  message-length maximum client auto
  message-length maximum 512
policy-map global_policy
 class inspection_default
  inspect dns migrated_dns_map_1 
  inspect ftp 
  inspect h323 h225 
  inspect h323 ras 
  inspect ip-options 
  inspect netbios 
  inspect rsh 
  inspect rtsp 
  inspect skinny  
  inspect esmtp 
  inspect sqlnet 
  inspect sunrpc 
  inspect tftp 
  inspect sip  
  inspect xdmcp 
!""".splitlines()

    active_delta = """policy-map global_policy
 class inspection_default
  inspect dns migrated_dns_map_1 
  inspect ftp 
  inspect h323 h225 
  inspect h323 ras 
  inspect ip-options 
  inspect netbios 
  inspect rsh 
  inspect rtsp 
  inspect skinny  
  inspect esmtp 
  inspect sqlnet 
  inspect sunrpc 
  inspect tftp 
  inspect sip  
  inspect xdmcp 
""".splitlines()
    
    res_backup = """!
class-map inspection_default
 match default-inspection-traffic
!
!
policy-map global_policy
 class inspection_default
  inspect ftp 
  inspect h323 h225 
  inspect h323 ras 
  inspect ip-options 
  inspect netbios 
  inspect rsh 
  inspect rtsp 
  inspect skinny  
  inspect esmtp 
  inspect sqlnet 
  inspect sunrpc 
  inspect tftp 
  inspect sip  
  inspect xdmcp 
policy-map type inspect dns migrated_dns_map_2
 parameters
  message-length maximum client auto
  message-length maximum 512
policy-map type inspect dns migrated_dns_map_1
 parameters
  message-length maximum client auto
  message-length maximum 512
!""".splitlines()

    reserve_delta = """policy-map global_policy
 class inspection_default
  inspect ftp 
  inspect h323 h225 
  inspect h323 ras 
  inspect ip-options 
  inspect netbios 
  inspect rsh 
  inspect rtsp 
  inspect skinny  
  inspect esmtp 
  inspect sqlnet 
  inspect sunrpc 
  inspect tftp 
  inspect sip  
  inspect xdmcp 
policy-map type inspect dns migrated_dns_map_2
 parameters
  message-length maximum client auto
  message-length maximum 512
""".splitlines()

    # commands = create_commands(act_backup, res_backup, active_delta, reserve_delta)
    # assert "no policy-map type inspect dns migrated_dns_map_2" in commands
    # assert "policy-map global_policy" in commands
    # intersections = intersection(act_backup, res_backup, active_delta, reserve_delta)

    # print()
    # print('\n'.join(intersections))
    # print()
    # print()
    # print('\n'.join(commands))
    # print()
