import keyring

import os
import sys
import pickle
import logging
from functions.connections import Multicontext
from functions.load_config import load_config
from loguru import logger

log_config = {
    "handlers": [
        {"sink": sys.stdout},
        {"sink": "fw_cfg_sync/logs/fw_cfg_sync_{time}.log", 
        "retention": "30 days", 
        'backtrace': True, 
        'diagnose': True},
    ]
}
logger.configure(**log_config)

# logger.add("fw_cfg_sync/logs/fw_cfg_sync_{time}.log", retention="30 days", backtrace=True, diagnose=True)
logger.debug("That's it, beautiful and simple logging!")
# logging.basicConfig(filename="fw_cfg_sync/logs/netmiko.log", level=logging.DEBUG)
# logger = logging.getLogger("netmiko")


def set_roles(inv):
    # TODO
    # active = Multicontext(conn = inv.devices["fw_a"]["connection"], name = inv.devices["fw_a"].get("name"))
    active = Multicontext(conn = inv.devices["fw_a"]["connection"])
    standby = Multicontext(conn = inv.devices["fw_b"]["connection"], name = inv.devices["fw_b"].get("name"))
    # standby = Multicontext(conn = inv.devices["fw_b"]["connection"])
    return active, standby


dirname = os.path.dirname(__file__)
p = os.path.join(dirname, "inventory", "multicontext.yaml")
inv = load_config(p)
active, standby = set_roles(inv)
for device in active, standby:
    device.check_reachability()
    if not device.is_reachable:
        pass
        # mail() #TODO

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

p = keyring.get_password("fw1", "aaa")
print(p)
