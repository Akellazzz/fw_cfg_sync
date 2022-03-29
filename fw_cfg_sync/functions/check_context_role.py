def check_context_role(firewalls, routers, inv):
    """ устанавливает роль контекста"""

    error = ""
            
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
