from ciscoconfparse import CiscoConfParse
from helpers import PARSE_DICT


def config_parser(parse, template):

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


def config_parser_sum(file_):
    with open(file_, "r") as f:
        parse = CiscoConfParse(f.readlines())
    result = []
    for template in PARSE_DICT.values():
        res = []
        res = config_parser(parse, template)
        for i in res:
            result.append("\n".join(i.ioscfg))
    return result


def create_cfg_for_standby(active_fw_cfg_file: str, cfg_for_standby_file: str):
    """Создает конфиг для standby МСЭ.
    Парсит файл active_fw_cfg_file, выделяет из него необходимые команды и сохраняет в cfg_for_standby_file"""
    result = config_parser_sum(active_fw_cfg_file)
    result = [i.replace("\n\n", "\n") for i in result]
    with open(cfg_for_standby_file, "w") as f:
        f.writelines(result)
