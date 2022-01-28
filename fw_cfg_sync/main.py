import os
import yaml
import sys
from functions.connections import Multicontext
from functions.load_config import load_inventory, load_mail_config
from functions.send_mail import send_mail
from argparse import ArgumentParser, RawTextHelpFormatter
from functions.find_delta import find_delta
from datetime import datetime
from copy import deepcopy
from loguru import logger


def getargs():
    modes = ["sync", "check"]
    reports = ["cli", "mail"]
    parser = ArgumentParser(
        description=f"""Программа синхронизации конфигураций МСЭ между площадками.
Документация - wiki""",
        formatter_class=RawTextHelpFormatter,
    )  # TODO
    parser.add_argument(
        "-v",
        "--verbose",
        help="Уровень логирования - DEBUG (по умолчанию - INFO)",
        action="store_true",
    )
    parser.add_argument(
        "-f",
        dest="filename",
        type=str,
        help="инвентарный файл из каталога /inventory",
        required=True,
    )

    # parser.add_argument("-m", dest="mode", type=str, help=f"{modes}", required=True)
    # parser.add_argument("-r", dest="report", type=str, help=f"{reports}", required=True)
    return parser.parse_args()


def get_inventory(inv):
    '''
    '''
    # TODO
    devices = []
    for device in inv.devices:
        # active = Multicontext(
        #     name=inv.devices["fw_a"].get("name"),
        #     host=inv.devices["fw_a"]["connection"]["host"],
        #     username=inv.devices["fw_a"]["connection"]["username"],
        #     device_type=inv.devices["fw_a"]["connection"]["device_type"],
        #     enable_required=inv.devices["fw_a"]["connection"]["enable_required"],
        # )
        devices.append(
            Multicontext(
                name=inv.devices[device].get("name"),
                host=inv.devices[device]["connection"]["host"],
                username=inv.devices[device]["connection"]["username"],
                device_type=inv.devices[device]["connection"]["device_type"],
                fast_cli=inv.devices[device]["connection"]["fast_cli"],
                enable_required=inv.devices[device]["connection"]["enable_required"],
            )
        )

    return devices



def main():

    # среда dev/prod
    environment = os.environ.get('FW-CFG-SYNC_ENVIRONMENT')

    # путь к конфигурации программы
    app_config_path = os.environ.get('FW-CFG-SYNC_APP_CONFIG')

    # директория для сохранения логов
    app_log_dir = os.environ.get('FW-CFG-SYNC_LOGDIR')

    # # путь к основной директории
    # main_dir = os.path.dirname(sys.argv[0])  

        
    args = getargs()
    datetime_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    logfilename = f'fw_cfg_sync_{datetime_now}.log'
    logfile = os.path.join(app_log_dir, logfilename)
    log_config = {
        "handlers": [
            {
                "sink": logfile,
                # "sink": f"{logs_dir}" + "/fw_cfg_sync_{time}.log",
                "retention": "30 days",
                "backtrace": True,
                "diagnose": True,
                "encoding": "utf-8"
            },
        ]
    }
    logger.configure(**log_config)
    if args.verbose:
        logger.add(sys.stdout, level="DEBUG")
    else:
        logger.add(sys.stdout, format="{message}", level="INFO")
    # 2022-01-09T19:43:02.912262+0300 INFO No matter added sinks, this message is not displayed
    # logger.remove()

    if not app_config_path:
        msg = "В переменных среды не найдена FW-CFG-SYNC_APP_CONFIG, указывающая путь к конфигурации программы"
        logger.error(msg)
        sys.exit(msg)
        
    app_config = os.path.join(app_config_path, "app_config.yaml")
    mail_config = load_mail_config(app_config)
    attached_files = [logfile]

    inv_path = os.path.join(app_config_path, "inventory", args.filename)
    inv = load_inventory(inv_path)

    devices = get_inventory(inv)
    
    for fw in devices:
        fw.check_reachability()
        if not fw.is_reachable:
            msg = f"Не удалось подключиться к {fw.name}"
            send_mail(msg, files = [logfile], **mail_config.dict()) 
            sys.exit(msg)


    for fw in devices:
        fw.get_contexts()
    #     for context in fw.contexts:
    #         fw.is_active = check_role(context)  # if it's active site sets fw.is_active = True  else False
        

    for fw in devices:
        for context in fw.contexts:
            fw.get_context_backup(context)
            fw.save_backup_to_file(context, datetime_now)

    if environment == 'dev':
        active_fw = deepcopy(devices[0])
        standby_fw = deepcopy(devices[0])
        for context in standby_fw.contexts:
            standby_fw.contexts[context]["backup_path"] = "C:\\Users\\eekosyanenko\\Documents\\fw_cfg_sync\\fw_configs\\asa2\\test1_2022-01-25_18-51-21.txt"


    elif environment == 'prod':
        with open(app_config, "r", encoding='utf-8') as stream:
            try:
                cfg = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        active_name = cfg["prod_env_temp_vars"]["active_fw"]
        standby_name = cfg["prod_env_temp_vars"]["standby_fw"]
        for fw in devices:
            if fw.name == active_name:
                active_fw = fw
            elif fw.name == standby_name:
                standby_fw = fw


    assert active_fw.contexts.keys() == standby_fw.contexts.keys()

    for context in active_fw.contexts:
        commands_for_standby = ""
        uniq_in_active, uniq_in_standby = find_delta(
            "active",
            active_fw.contexts[context]["backup_path"],
            "standby",
            standby_fw.contexts[context]["backup_path"],
        )
        if uniq_in_standby:
            msg = f"На резервном МСЭ {standby_fw.name}-{context} найдены команды, которых нет на активном МСЭ \n{uniq_in_standby}" 
            logger.error(msg)
            logger.error(f"Выход")
            send_mail(msg, files = [logfile], **mail_config.dict()) 
            sys.exit()
            # TODO
        elif uniq_in_active:

            backup_dir = os.environ.get('FW-CFG-SYNC_BACKUPS')
            uniq_in_active_filename = context + "_" + datetime_now + "_new_commands.txt"
            commands_for_standby = os.path.join(backup_dir, standby_fw.name, uniq_in_active_filename)

            with open(commands_for_standby, "w") as f:
                f.write(uniq_in_active)
                logger.info(
                    f"Дельта для {standby_fw.name}-{context} сохранена в файл {commands_for_standby}"
                )
            attached_files.append(commands_for_standby)
        elif (not uniq_in_standby) and (not uniq_in_active):
            logger.info(
                f"Конфигурации контекста {context} МСЭ {active_fw.name}/{standby_fw.name} равны"
            )

    
    
    send_mail('Лог во вложении', files = attached_files, **mail_config.dict())
    pass


if __name__ == "__main__":
    main()
