from copy import deepcopy
import yaml


def check_role(environment, app_config, devices):
    """
    Роль должна определяться для каждого контекста и проверяться, что все контексты файрвола имеют одну роль
    """
    # TODO

    if environment == "dev":
        active_fw = deepcopy(devices[0])
        standby_fw = deepcopy(devices[0])
        for context in standby_fw.contexts:
            standby_fw.contexts[context][
                "backup_path"
            ] = "C:\\Users\\eekosyanenko\\Documents\\fw_cfg_sync\\fw_configs\\asa2\\test1_2022-01-25_18-51-21.txt"

    elif environment == "prod":
        with open(app_config, "r", encoding="utf-8") as stream:
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

    assert (
        active_fw.contexts.keys() == standby_fw.contexts.keys()
    )  # TODO выводить сообщение в лог и выходить

    return active_fw, standby_fw
