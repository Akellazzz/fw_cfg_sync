import keyring

import os
import sys
import pickle
import logging
from functions.connections import Multicontext
from functions.load_config import load_config
from loguru import logger

main_dir = os.path.dirname(sys.argv[0]) # путь к главной директории 
logs_dir = os.path.join(main_dir, "logs") 

log_config = {
    "handlers": [
        {"sink": sys.stdout},
        {"sink": f"{logs_dir}" + "/fw_cfg_sync_{time}.log", 
        "retention": "30 days", 
        'backtrace': True, 
        'diagnose': True},
    ]
}
logger.configure(**log_config)


def set_roles(inv):
    # TODO
    active = Multicontext(
        name = inv.devices["fw_a"].get("name"),
        host = inv.devices["fw_a"]["connection"]["host"],
        username = inv.devices["fw_a"]["connection"]["username"],
        device_type = inv.devices["fw_a"]["connection"]["device_type"],
        enable_required = inv.devices["fw_a"]["connection"]["enable_required"]
        )
    standby = Multicontext(
        name = inv.devices["fw_b"].get("name"),
        host = inv.devices["fw_b"]["connection"]["host"],
        username = inv.devices["fw_b"]["connection"]["username"],
        device_type = inv.devices["fw_b"]["connection"]["device_type"],
        enable_required = inv.devices["fw_b"]["connection"]["enable_required"]
        )
    
    return active, standby


dirname = os.path.dirname(__file__)
p = os.path.join(dirname, "inventory", "multicontext.yaml")
inv = load_config(p)
active, standby = set_roles(inv)
# for device in active, standby:
#     device.check_reachability()
#     if not device.is_reachable:
#         pass
#         # mail() #TODO

active.get_contexts()
for context in active.contexts:
    active.get_context_backup(context)
    active.save_backup_to_file(context)

# with open("fw_cfg_sync\\tests\\fw_configs\\pickle_dumps\\active_with_backups2.pickle", 'wb') as f:
#     pickle.dump(active, f)
# with open("fw_cfg_sync\\tests\\fw_configs\\pickle_dumps\\standby_unreacheble.pickle", 'wb') as f:
#     pickle.dump(standby, f)

# with open("fw_cfg_sync\\tests\\fw_configs\\pickle_dumps\\active_with_backups2.pickle", 'rb') as f:
#     active = pickle.load(f)
# with open("fw_cfg_sync\\tests\\fw_configs\\pickle_dumps\\standby_unreacheble.pickle", 'rb') as f:
#     standby = pickle.load(f)


# keyring.set_password("fw1", "aaa", "aaa")
# p = keyring.get_password("fw1", "aaa")
# print(p)
pass