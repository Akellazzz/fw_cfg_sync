from typing import Optional
from ciscoconfparse import CiscoConfParse
from loguru import logger
from pprint import pprint
# from .find_delta import get_parser_config, block_parser, get_uniq
# from find_delta import get_parser_config, block_parser, get_uniq
from functions.find_delta import get_parser_config, block_parser
import yaml
import os


def active_only_commands(active_config: list, reserve_config: list, active_delta: list, reserve_delta: list) -> list:
    ''' Ищет блоки конфигурации, которые есть только в активном контексте
    
    Возвращает список команд в том же порядке, что и шаблоны в parser_config
    '''
    commands = []
    parser_config = get_parser_config()
    for i in parser_config:    
        if i == 'access-list': 
            commands += acls_to_be_created(active_config, reserve_config, active_delta, reserve_delta)
            continue
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
            continue
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


def intersection(active_config: list, reserve_config: list, active_delta: list, reserve_delta: list) -> list:
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
        if i == 'access-list': 
            commands += create_acl_changes(active_config, reserve_config, active_delta, reserve_delta)
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

                    block_intersection = res_block_parse.sync_diff(act_block.ioscfg, '')
                    if block_intersection:

                        if len(block_intersection) > 1:
                            intersection = list(dict.fromkeys(block_intersection)) # Remove Duplicates
                            cmd_tmp_list = [] 
                            parent = block_intersection[0] # parent
                            children = block_intersection[1::]
                            children = sorted(children, key=lambda a: a.strip().startswith('no ')) # команды на удаление в конец списка
                            cmd_tmp_list = [parent] + children

                            commands += cmd_tmp_list
                        else:
                            commands += block_intersection

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


def create_acl_changes(active_config: list, reserve_config: list, active_delta: list, reserve_delta: list) -> list:
    ''' формирует команды ACL для случая, если ACL с одним именем есть на обоих контекстах и их строки различаются 
    '''

    change = []
    act_delta_acl_names = set(get_acl(active_delta).keys())
    res_delta_acl_names = set(get_acl(reserve_delta).keys())
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

            if acl_act_lines[0].strip() != acl_res_lines[0].strip():
                # когда в ACL отличается первая же строка, сначала добавить новую фейковую
                fake_acl = f'access-list {name} deny icmp host 1.1.1.1 host 1.1.1.1'
                change += [fake_acl]
                # удалить остальные
                change += [f'no {line}' for line in acl_res_lines] 
                # прописать новые
                change += acl_act_lines
                # удалить фейковую
                change += [f'no {fake_acl}']

                continue

            # if len(acl_act_lines) == 1:
            #     # когда в ACL одна строка и она отличается, нужно сначала добавить новую, а потом удалить старую
            #     change += [acl_act_lines[0]]
            #     change += [f'no {acl_res_lines[0]}'] 
            #     continue
            
            
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
            else:
                if i <= len(acl_res_lines):
                    # если все прошедшие строки равны и на резервном контексте больше строк, чем на активном, оставшиеся нужно удалить
                    i += 1
                    change += [f'no {line}' for line in acl_res_lines[i::]]
                    
    return change


def create_commands(active_config: list, reserve_config: list, active_delta: list, reserve_delta: list):
    ''' формирует список команд для отправки на резервный контекст
    
    Порядок применения команд важен:
    
    commands - команды для переноса блоков конфигурации, которые есть только на активном контексте (в т. ч. уникальные ACL). Порядок как в parser_config

    no_commands - удаление блоков конфигурации, которые есть только в резервном контексте. Порядок, обратный parser_config

    atomic_changes - команды для переноса блоков конфигурации,в которых есть одинаковый parent. 
    Переносит на резервный контекст в соответствующий parent недостающие команды и удаляет лишние. 
    Если ACL с одним именем есть на обоих контекстах и их строки различаются - добавляет и удаляет строки в ACL.
    '''

    commands = active_only_commands(active_config, reserve_config, active_delta, reserve_delta)
    # acl_commands = create_acl(active_config, active_delta)
    # acl_changes = create_acl_changes(active_config, reserve_config, active_delta, reserve_delta)
    no_commands = negate_reserve_only_commands(active_config, reserve_config, active_delta, reserve_delta)
    atomic_changes = intersection(active_config, reserve_config, active_delta, reserve_delta)
    
    # return commands + acl_commands + no_commands + atomic_changes
    return commands + no_commands + atomic_changes



def create_commands_from_files(active_config: str, reserve_config: str, active_delta: Optional[str], reserve_delta: Optional[str]):
    ''' Ожидает на вход пути к файлам и формирует список команд для отправки на резервный контекст'''


    with open(active_config) as act:
        act_config_list = act.readlines()
        act_config_list = [i.rstrip() for i in act_config_list]
    with open(reserve_config) as res:
        res_config_list = res.readlines()
        res_config_list = [i.rstrip() for i in res_config_list]
    if active_delta:
        with open(active_delta) as act_delta:
            act_delta_list = act_delta.readlines()
            act_delta_list = [i.rstrip() for i in act_delta_list]
    else:
        act_delta_list = []
    if reserve_delta:
        with open(reserve_delta) as res_delta:
            res_delta_list = res_delta.readlines()
            res_delta_list = [i.rstrip() for i in res_delta_list]
    else:
        res_delta_list = []
    commands = create_commands(act_config_list, res_config_list, act_delta_list, res_delta_list)


    return commands 


def create_commands_for_reserve_context(firewalls, datetime_now) :
    
    common_contexts = set(firewalls[0].contexts).intersection(set(firewalls[1].contexts))
    for context in common_contexts:

            if firewalls[0].contexts[context].get("role") == 'active' and firewalls[1].contexts[context].get("role") == 'reserve':
                active = firewalls[0]
                reserve = firewalls[1]
            elif firewalls[0].contexts[context].get("role") == 'reserve' and firewalls[1].contexts[context].get("role") == 'active':
                active = firewalls[1]
                reserve = firewalls[0]
            else:
                raise

            active_config =active.contexts[context].get('backup_path')
            reserve_config = reserve.contexts[context].get('backup_path')
            active_delta = active.contexts[context].get('delta_path')
            reserve_delta = reserve.contexts[context].get('delta_path')
            if active_delta or reserve_delta:
                commands_for_reserve_context = create_commands_from_files(active_config, reserve_config, active_delta, reserve_delta)
                # print(commands_for_reserve_context)
                backup_dir = os.environ.get("FW-CFG-SYNC_BACKUPS")

                commands_filename = (f'{reserve.name}-{context}_{datetime_now}_commands.txt')
                commands_fullpath = os.path.join(backup_dir, reserve.name, commands_filename)
                with open(commands_fullpath, "w") as f:
                    f.write('\n'.join(commands_for_reserve_context))
                logger.info(
                    f"Команды для {reserve.name}-{context} сохранены в файл {commands_fullpath}"
                )
                reserve.contexts[context]["commands_path"] = commands_fullpath
            else:
                logger.info(
                    f"Команды для контекста {reserve.name}-{context} не созданы, т. к. отсутствует дельта"
                )

