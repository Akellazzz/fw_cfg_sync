from ciscoconfparse import CiscoConfParse
from loguru import logger
import yaml
import os


def get_parser_config():
    app_config_path = os.environ.get('FW-CFG-SYNC_APP_CONFIG')
    config_file = os.path.join(app_config_path, 'parser_config.yaml')
    logger.debug(f"Конфигурация парсера: {config_file} ")

    with open(config_file) as f:
        parser_config = yaml.safe_load(f)
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


def find_delta(name1: str, file1: str, name2: str, file2: str) -> tuple:
    ''' Возвращает команды конфигурации, уникальные для каждого из МСЭ
    
        Parameters
        ----------
        name1 - Имя МСЭ 1

        file1 - Путь к файлу конфигурации МСЭ 1

        name2 - Имя МСЭ 2

        file2 - Путь к файлу конфигурации МСЭ 2

        Returns
        -------
        Кортеж из 2 элементов с конфигурацией, уникальной для МСЭ 1 и МСЭ 2 соответственно

    '''
    file1_uniq = ''
    file2_uniq = ''
    parser_config = get_parser_config()
    with open(file1, "r") as f1, open(file2, "r") as f2:
        parse1 = CiscoConfParse(f1.readlines())
        parse2 = CiscoConfParse(f2.readlines())
    for block in parser_config:
        template = parser_config[block].get('template')
        res1 = set(tuple(i.ioscfg) for i in block_parser(parse1, template))
        res2 = set(tuple(i.ioscfg) for i in block_parser(parse2, template))
        if res1 == res2:
            logger.debug(f"{block:<20} OK")

        else:
            logger.debug(f"{block:<20} FAIL")

            diff = res1 ^ res2
            if diff:
                file1_only = res1.difference(res2)
                file2_only = res2.difference(res1)

                if file1_only:
                    logger.debug(f"---- Только в {name1}:")
                    file1_out = str()
                    for i in list(file1_only):
                        file1_out += "".join(i)
                        # file1_out += "!"
                    file1_uniq += file1_out
                    logger.debug(file1_out)

                if file2_only:
                    logger.debug(f"---- Только в {name2}:")

                    file2_out = str()
                    for i in list(file2_only):
                        file2_out += "".join(i)
                        # file2_out += "!"
                    file2_uniq += file2_out
                    logger.debug(file2_out)

    return file1_uniq, file2_uniq



# file1_uniq, file2_uniq = find_delta(
#     "active",
#     "C:\\Users\\eekosyanenko\\Documents\\fw_cfg_sync\\fw_configs\\asa2\\test1_2022-01-27_16-06-31.txt",
#     "standby",
#     "C:\\Users\\eekosyanenko\\Documents\\fw_cfg_sync\\fw_configs\\asa2\\test1_2022-01-25_18-51-21.txt"
# )
# pass                    