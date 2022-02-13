from ciscoconfparse import CiscoConfParse
from loguru import logger
from pprint import pprint
from find_delta import get_parser_config, block_parser, get_uniq
import yaml
import os


active_delta = """!
object-group protocol obj_prot0
 description test_og_prot
 protocol-object icmp
!
object-group protocol obj_prot1
 description test_og_prot
 protocol-object icmp
!
interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0
!
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
interface GigabitEthernet0/1
 ip address 172.16.1.1 255.255.255.0
 no ip proxy-arp
!
access-list res_only extended deny ip object-group og0 host 8.8.8.8 
!""".splitlines()


def active_only_commands(active_delta: list, reserve_delta: list) -> list:
    ''' Ищет блоки конфигурации, которые есть только в активном контексте
    
    Возвращает список команд
    '''
    commands = []
    parser_config = get_parser_config()
    for i in parser_config:    
        template = parser_config[i].get("template")
        act_blocks = block_parser(CiscoConfParse(active_delta), template)
        res_blocks = block_parser(CiscoConfParse(reserve_delta), template)

        res_parents = [i.text for i in res_blocks]

        for act_parent_and_children in act_blocks:
            act_parent = act_parent_and_children.text
            if act_parent_and_children.ioscfg and act_parent not in res_parents:
                # если в активном контексте есть блоки с parent, которых нет на резервном, добавляет их в конфиг вместе с children
                commands += act_parent_and_children.ioscfg
    if commands:
        commands.append('!')
    return commands


def negated_reserve_only_commands(active_delta: list, reserve_delta: list) -> list:
    ''' Ищет блоки конфигурации, которые есть только в резервном контексте
    
    Возвращает список команд, удаляющий эти блоки
    '''
    negate_commands = []
    parser_config = get_parser_config()
    for i in parser_config:    
        block_negate_commands = []
        template = parser_config[i].get("template")
        act_blocks = block_parser(CiscoConfParse(active_delta), template)
        res_blocks = block_parser(CiscoConfParse(reserve_delta), template)

        act_parents = [i.text for i in act_blocks]

        for res_parent_and_children in res_blocks:
            res_parent = res_parent_and_children.text
            if res_parent not in act_parents:
                # если в резервном контексте есть блоки с parent, которых нет на активном, добавляет к parent 'no ...'
                block_negate_commands.append('no '+ res_parent)
        if block_negate_commands:
            negate_commands.append(block_negate_commands)
    # print(negate_commands)

    # реверс списка, чтобы access-list удалялись перед используемыми ими object-group и т. п.
    negate_commands.reverse()

    result = []
    for list_ in negate_commands:
        result += list_ 

    if result:
        result.append('!')

    return result 

def intersection(active_delta: list, reserve_delta: list) -> list:
    ''' Ищет в активном и резервном контекстах блоки конфигурации, в которых есть одинаковый parent
    
    Возвращает список команд, который переносит в parent недостающие команды и удаляет лишние.
    
    active:
    !
    object-group protocol obj_prot0
     description test_og_prot
     protocol-object icmp
    !

    reserve:
    !
    object-group protocol obj_prot0
     description test_og_prot
     protocol-object udp
    !

    result:
    ['object-group protocol obj_prot0', ' no protocol-object udp', 'object-group protocol obj_prot0', ' protocol-object icmp', '!']   

    В результате лишний раз вызывается object-group protocol obj_prot0 - так делает sync_diff
    http://pennington.net/tutorial/ciscoconfparse/ccp_tutorial.html#slide14  
    '''
    commands = []
    parser_config = get_parser_config()
    for i in parser_config:    
        template = parser_config[i].get("template")

        act_blocks = block_parser(CiscoConfParse(active_delta), template)
        res_blocks = block_parser(CiscoConfParse(reserve_delta), template)

        res_parents = [i.text for i in res_blocks]
        active_block_commands_list = []
        for block in act_blocks:
            active_block_commands_list += block.ioscfg 

        for block in act_blocks:
            act_parent = block.text
            if act_parent in res_parents:
                res_index = res_parents.index(act_parent)
                res_block = res_blocks[res_index]
                res_block_parse = CiscoConfParse(res_block.ioscfg, template)
                intersection = res_block_parse.sync_diff(active_block_commands_list, '')
                if intersection:
                    commands += intersection
    if commands:
        commands.append('!')

    return commands


def create_commands(active_delta, reserve_delta):
    commands = active_only_commands(active_delta, reserve_delta)
    no_commands = negated_reserve_only_commands(active_delta, reserve_delta)
    atomic_changes = intersection(active_delta, reserve_delta)
    
    return commands + no_commands + atomic_changes

if __name__ == '__main__':
    commands = create_commands(active_delta, reserve_delta)
    print("\n".join(commands))
