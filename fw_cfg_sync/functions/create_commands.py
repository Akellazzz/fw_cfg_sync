from ciscoconfparse import CiscoConfParse
from loguru import logger
from pprint import pprint
# from .find_delta import get_parser_config, block_parser, get_uniq
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


def active_only_commands(active_config: list, reserve_config: list, active_delta: list, reserve_delta: list) -> list:
    ''' Ищет блоки конфигурации, которые есть только в активном контексте
    
    Возвращает список команд
    '''
    commands = []
    parser_config = get_parser_config()
    for i in parser_config:    
        if i == 'access-list': 
            commands += acls_to_be_created(active_config, reserve_config, active_delta, reserve_delta)
        template = parser_config[i].get("template")
        act_blocks = block_parser(CiscoConfParse(active_delta), template)
        res_blocks = block_parser(CiscoConfParse(reserve_delta), template)

        res_parents = [i.text for i in res_blocks]

        for act_parent_and_children in act_blocks:
            act_parent = act_parent_and_children.text
            if act_parent_and_children.ioscfg and act_parent not in res_parents:
                # если в активном контексте есть блоки с parent, которых нет на резервном, добавляет их в конфиг вместе с children
                commands += act_parent_and_children.ioscfg
    return commands


def negate_reserve_only_commands(active_config: list, reserve_config: list, active_delta: list, reserve_delta: list) -> list:
    ''' Ищет блоки конфигурации, которые есть только в резервном контексте
    
    Возвращает список команд, удаляющий эти блоки
    '''
    negate_commands = []
    parser_config = get_parser_config()
    for i in parser_config:    
        if i == 'access-list': 
            negate_commands += acls_to_be_removed(active_config, reserve_config, active_delta, reserve_delta)
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

    # реверс списка, чтобы удаление проходило в правильном порядке
    negate_commands.reverse()

    result = []
    for list_ in negate_commands:
        result += list_ 

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
    ['object-group protocol obj_prot0', ' no protocol-object udp', ' protocol-object icmp', '!']   

    '''
    commands = []
    parser_config = get_parser_config()
    for i in parser_config:    
        if i == 'access-list': # пропуск, т. к. важен порядок ACL
            continue
        if parser_config[i].get("action") not in ['prepare', 'change']:
            continue
        template = parser_config[i].get("template")
        act_blocks = block_parser(CiscoConfParse(active_delta), template)
        res_blocks = block_parser(CiscoConfParse(reserve_delta), template)

        res_parents = [i.text for i in res_blocks]
        active_block_commands_list = []
        for block in act_blocks:
            active_block_commands_list += block.ioscfg 
        for act_block in act_blocks:
            # breakpoint()
            act_parent = act_block.text
            if act_parent in res_parents:

                index = res_parents.index(act_parent)
                res_block = res_blocks[index]
                act_block_parse = CiscoConfParse(act_block.ioscfg, template)
                res_block_parse = CiscoConfParse(res_block.ioscfg, template)
                if act_block_parse.ioscfg == res_block_parse.ioscfg:
                    continue
                else:

                    intersection = res_block_parse.sync_diff(act_block.ioscfg, '')
                    if intersection:

                        if len(intersection) > 1:
                            intersection = list(dict.fromkeys(intersection)) # Remove Duplicates
                            cmd_tmp_list = [] 
                            parent = intersection[0] # parent
                            children = intersection[1::]
                            children = sorted(children, key=lambda a: a.strip().startswith('no ')) # команды на удаление в конец списка
                            cmd_tmp_list = [parent] + children

                            commands += cmd_tmp_list
                        else:
                            commands += intersection

    return commands


def get_acl(config: list) -> dict:
    ''' формирует словарь вида {имя_ACL: [список строк ACL]} '''
    result = {}
    for line in config:
        if line.strip().startswith('access-list '):
            name = line.split()[1]
            if result.get(name):
                result[name].append(line)
            else:
                result[name] = [line]
    return result



# def create_acl(active_config: list, active_delta: list) -> list:
#     ''' выбирает из дельты ACL и формирует список команд access-list для отправки на резервный МСЭ 
#     '''
#     commands = []
#     all_acl_dict = get_acl(active_config)
#     delta_acl_names = list(get_acl(active_delta).keys())
#     for name in delta_acl_names:    
#             commands.append(f'clear configure access-list {name}')
#             commands += all_acl_dict[name]
#     return commands


def acls_to_be_removed(active_config: list, reserve_config: list, active_delta: list, reserve_delta: list) -> list:
    ''' формирует команды для удаления ACL, которые есть только на резервном контексте
    TODO нужно проверять, что если есть имя в reserve_delta и нет в active_delta, то имени нет и в active_config
    Если имя есть, то оно должно обрабатываться в create_acl_changes '''

    result = []
    act_delta_acl_names = set(get_acl(active_delta).keys())
    res_delta_acl_names = set(get_acl(reserve_delta).keys())

    all_delta_acl_names = act_delta_acl_names | res_delta_acl_names

    all_acl_act_dict = get_acl(active_config)
    all_acl_res_dict = get_acl(reserve_config)

    for name in all_delta_acl_names:
        if (name in res_delta_acl_names) and (name not in all_acl_act_dict.keys()):
            # если ACL есть только на резервном контексте, их нужно удалить
            del_acls = all_acl_res_dict.get(name)
            # delete += [f'no {line}' for line in del_acls if line.strip().startswith(f'access-list {name} ')]
            result += [f'no {line}' for line in del_acls if line.strip().startswith(f'access-list {name} ')]

    return result


def acls_to_be_created(active_config: list, reserve_config: list, active_delta: list, reserve_delta: list) -> list:
    ''' формирует команды для создания ACL с именами, которые есть только на активном контексте'''
    result = []

    act_delta_acl_names = set(get_acl(active_delta).keys())
    res_delta_acl_names = set(get_acl(reserve_delta).keys())
    act_only_acl_names = act_delta_acl_names - res_delta_acl_names
    all_delta_acl_names = act_delta_acl_names | res_delta_acl_names

    all_acl_act_dict = get_acl(active_config)
    all_acl_res_dict = get_acl(reserve_config)

    for name in all_delta_acl_names:
        if (name in act_delta_acl_names) and (name not in all_acl_res_dict.keys()):
            # если ACL есть только на активном контексте, то можно просто перенести его на резервный
            # create += all_acl_act_dict.get(name)
            result += all_acl_act_dict.get(name)
    
    return result


# def get_acl_names_from_delta(active_delta: list, reserve_delta: list) -> tuple:
#     act_delta_acl_names = set(get_acl(active_delta).keys())
#     res_delta_acl_names = set(get_acl(reserve_delta).keys())
#     common_acl_names = act_delta_acl_names & res_delta_acl_names
#     act_only_acl_names = act_delta_acl_names - res_delta_acl_names
#     res_only_acl_names = res_delta_acl_names - act_delta_acl_names 

#     return common_acl_names, act_only_acl_names, res_only_acl_names

def create_acl_changes(active_config: list, reserve_config: list, active_delta: list, reserve_delta: list) -> list:
    change = []

    act_delta_acl_names = set(get_acl(active_delta).keys())
    res_delta_acl_names = set(get_acl(reserve_delta).keys())
    act_only_acl_names = act_delta_acl_names - res_delta_acl_names
    res_only_acl_names = res_delta_acl_names - act_delta_acl_names 

    common_acl_names_in_delta = act_delta_acl_names & res_delta_acl_names
    all_delta_acl_names = act_delta_acl_names | res_delta_acl_names

    all_acl_act_dict = get_acl(active_config)
    all_acl_res_dict = get_acl(reserve_config)

    for name in all_delta_acl_names:
        if (name in act_delta_acl_names) and (name not in all_acl_res_dict.keys()):
            # если ACL есть только на активном контексте, то можно просто перенести его на резервный
            # случай обрабатывается в функции acls_to_be_created
            continue
        elif (name in res_delta_acl_names) and (name not in all_acl_act_dict.keys()):
            # если ACL есть только на резервном контексте, их нужно удалить
            # случай обрабатывается в функции acls_to_be_removed
            continue
        else:
        # elif name in common_acl_names_in_delta:
            # если ACL есть на обоих контекстах и их состав различается

            acl_act_lines = all_acl_act_dict.get(name)
            acl_res_lines = all_acl_res_dict.get(name)
            if len(acl_act_lines) == 1:
                # когда в ACL одна строка и она отличается, нужно сначала добавить новую, а потом удалить старую
                change += [acl_act_lines[0]]
                change += [f'no {acl_res_lines[0]}'] 
                continue
            
            
            for i in range(len(acl_act_lines)):
                if i <= len(acl_res_lines):
                    # каждая строка проверяется, пока не найдется различие или не закончатся строки на резервном
                    if acl_act_lines[i].strip() == acl_res_lines[i].strip():
                        # одинаковые строки пропускаются
                        continue
                    else:
                        # если нашлось расхождение
                        # сначала нужно удалить строки, т. к. могут быть дубликаты 
                        change += [f'no {line}' for line in acl_res_lines[i::]] 

                        # добавляем все оставшиеся с активного
                        change += acl_act_lines[i::]
                        break
            if i <= len(acl_res_lines):
                # если все прошедшие строки равны и на резервном контексте больше строк, чем на активном, оставшиеся нужно удалить
                i += 1
                change += [f'no {line}' for line in acl_res_lines[i::]]
                    
    return change





def create_commands(active_config: list, reserve_config: list, active_delta: list, reserve_delta: list):
    commands = active_only_commands(active_config, reserve_config, active_delta, reserve_delta)
    # acl_commands = create_acl(active_config, active_delta)
    acl_changes = create_acl_changes(active_config, reserve_config, active_delta, reserve_delta)
    no_commands = negate_reserve_only_commands(active_config, reserve_config, active_delta, reserve_delta)
    atomic_changes = intersection(active_delta, reserve_delta)
    
    # return commands + acl_commands + no_commands + atomic_changes
    return commands + acl_changes + no_commands + atomic_changes

if __name__ == '__main__':

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

    x = create_acl_changes(active_config, reserve_config, active_delta, reserve_delta)
    print(x)
    # pprint(intersection(active_delta, reserve_delta))
    # commands = create_commands(active_delta, reserve_delta)
    # print("\n".join(commands))
