from copy import deepcopy
import yaml
from functions.send_mail import send_mail


def check_context_role(environment, app_config, firewalls, routers, inv):
    """
    Роль определяется для каждого контекста, т. к. не все могут быть активными на одной площадке
    """
    # TODO
    error = ""
    if environment == "dev":
        # active_fw = deepcopy(firewalls[0])
        # reserve_fw = deepcopy(firewalls[0])
        # for context in reserve_fw.contexts:
        #     reserve_fw.contexts[context][
        #         "backup_path"
        #     ] = "C:\\Users\\eekosyanenko\\Documents\\fw_cfg_sync\\fw_configs\\asa2\\test1_2022-01-25_18-51-21.txt"
        pass
                
            #   test1:
            #     device: router1
            #     command: show route
            #     find_string: 0.0.0.0
            #     site: active
            #     # site: reserve
                
        for context in firewalls[0].contexts:
            for router in routers:
                if inv.contexts_role_check[context]['device'] == router.name:

                    active_sign = inv.contexts_role_check[context].get('is_active')
                    reserve_sign = inv.contexts_role_check[context].get('is_reserve')

                    cmd = inv.contexts_role_check[context]['command']
                    response = router.send_command(cmd)

                    if active_sign in response or reserve_sign in response:
                        if active_sign in response:
                            firewalls[0].contexts[context] = {"role": "active"}
                            firewalls[1].contexts[context] = {"role": "reserve"}
                        if reserve_sign in response:
                            firewalls[0].contexts[context] = {"role": "reserve"}
                            firewalls[1].contexts[context] = {"role": "active"}
                    else:
                        error = f"Не удалось определить роли контекста {context}. На {router.name} в выводе команды {cmd} не найдено '{active_sign}' или '{reserve_sign}'"
                        return firewalls, error

        return firewalls, error

    # elif environment == "prod":
    #     with open(app_config, "r", encoding="utf-8") as stream:
    #         try:
    #             cfg = yaml.safe_load(stream)
    #         except yaml.YAMLError as exc:
    #             print(exc)
    #     active_name = cfg["prod_env_temp_vars"]["active_fw"]
    #     reserve_name = cfg["prod_env_temp_vars"]["reserve_fw"]
    #     for fw in firewalls:
    #         if fw.name == active_name:
    #             active_fw = fw
    #         elif fw.name == reserve_name:
    #             reserve_fw = fw

    # assert (
    #     active_fw.contexts.keys() == reserve_fw.contexts.keys()
    # )  # TODO выводить сообщение в лог и выходить

    # return active_fw, reserve_fw
