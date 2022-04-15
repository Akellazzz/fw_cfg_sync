from ciscoconfparse import CiscoConfParse
from loguru import logger
import yaml
import os


def get_parser_config(*args) -> dict:
    ''' Считывает конфиг парсера из файла, указанного в переменной среды FW-CFG-SYNC_APP_CONFIG
    
    args - фильтры для поля action

    Примеры:
    get_parser_config() - все объекты без фильтрации
    get_parser_config('sync') - только объекты c action: sync
    '''

    if not set(args).issubset({'find', 'sync'}):
        raise KeyError(f'Неправильный фильтр {args} для get_parser_config')

    app_config_path = os.environ.get("FW-CFG-SYNC_APP_CONFIG")
    config_file = os.path.join(app_config_path, "parser_config.yaml")
    # logger.debug(f"Конфигурация парсера: {config_file} ")

    with open(config_file) as f:
        parser_config = yaml.safe_load(f)
    if args:
        return {k:v for k,v in parser_config.items() if v.get('action') in args}
    else:
        return parser_config


def block_parser(parse, template):

    if isinstance(template, dict):
        mode = template.get("find_obj_mode")
    else:
        mode = None
    if mode:
        p = template.get("parentspec")
        c = template.get("childspec")

    if mode == "without":
        res = parse.find_objects_wo_child(parentspec=p, childspec=c)
    elif mode == "with":
        res = parse.find_objects_w_child(parentspec=p, childspec=c)
    else:
        res = parse.find_objects(f"{template}")
    return res


def get_uniq(parse1, parse2, template):
    res1 = [tuple(i.ioscfg) for i in block_parser(parse1, template)]
    res2 = [tuple(i.ioscfg) for i in block_parser(parse2, template)]
    file1_uniq = [i for i in res1 if i not in res2]
    file2_uniq = [i for i in res2 if i not in res1]
    return file1_uniq, file2_uniq


def find_delta(file1: str, file2: str) -> tuple[str, str]:
    """Возвращает команды конфигурации, уникальные для каждого из МСЭ

    Parameters
    ----------
    file1 - Путь к файлу конфигурации МСЭ 1

    file2 - Путь к файлу конфигурации МСЭ 2

    Returns
    -------
    Дельты для МСЭ 1 и МСЭ 2 

    """
    file1_result = ""
    file2_result = ""
    parser_config = get_parser_config()
    with open(file1, "r") as f1, open(file2, "r") as f2:
        parse1 = CiscoConfParse(f1.readlines())
        parse2 = CiscoConfParse(f2.readlines())
    for block in parser_config:
        template = parser_config[block].get("template")
        file1_uniq, file2_uniq = get_uniq(parse1, parse2, template)

        if file1_uniq:
            file1_out = str()
            for parent_and_children in file1_uniq:
                file1_out += "".join(parent_and_children)
            file1_result += file1_out

        if file2_uniq:
            file2_out = str()
            for parent_and_children in file2_uniq:
                file2_out += "".join(parent_and_children)
            file2_result += file2_out

    return file1_result, file2_result


def create_diff_files(firewalls, datetime_now) -> set:
    
    common_contexts = set(firewalls[0].contexts).intersection(set(firewalls[1].contexts))
    for context in common_contexts:

        fw0_delta, fw1_delta = find_delta(
            firewalls[0].contexts[context]["backup_path"],
            firewalls[1].contexts[context]["backup_path"],
        )

        firewalls[0].contexts[context]["delta"] = fw0_delta
        firewalls[1].contexts[context]["delta"] = fw1_delta

        for fw in firewalls:
            if fw.contexts[context]["delta"]:
                backup_dir = os.environ.get("FW-CFG-SYNC_BACKUPS")
                role = fw.contexts[context]["role"]
                delta = fw.contexts[context]["delta"]
                delta_filename = (f'{fw.name}-{context}_{datetime_now}_{role}_delta.txt')
                delta_fullpath = os.path.join(backup_dir, fw.name, delta_filename)

                with open(delta_fullpath, "w") as f:
                    f.write(delta)
                logger.info(
                    f"Дельта {fw.name}-{context} (роль - {role}) сохранена в файл {delta_fullpath}"
                )
                fw.contexts[context]["delta_path"] = delta_fullpath

        if (not fw0_delta) and (not fw1_delta):
            logger.info(
                f"Конфигурации контекста {context} МСЭ {firewalls[0].name}/{firewalls[1].name} равны"
            )

    return firewalls

