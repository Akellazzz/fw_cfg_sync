from datetime import datetime
from netmiko import ConnectHandler

from functions.connections import Multicontext
import os
import pickle
import logging
from functions.load_config import load_config

logging.basicConfig(filename="fw_cfg_sync/logs/netmiko.log", level=logging.DEBUG)
logger = logging.getLogger("netmiko")


def set_roles(inv):
    # TODO
    # active = Multicontext(conn = inv.devices["fw_a"]["connection"], name = inv.devices["fw_a"].get("name"))
    active = Multicontext(conn = inv.devices["fw_a"]["connection"])
    standby = Multicontext(conn = inv.devices["fw_a"]["connection"], name = inv.devices["fw_a"].get("name"))
    # standby = Multicontext(conn = inv.devices["fw_b"]["connection"])
    return active, standby


# dirname = os.path.dirname(__file__)
# p = os.path.join(dirname, "inventory", "multicontext.yaml")
# inv = load_config(p)
# active, standby = set_roles(inv)
# active.get_contexts()
# for context in active.contexts:
#     active.get_context_backup(context)
#     active.save_backup_to_file(context)

with open("fw_cfg_sync\\tests\\fw_configs\\pickle_dumps\\active_with_backups.pickle", 'rb') as f:
    active = standby = pickle.load(f)


cmd = "sh int ip br"
for fw in (active, standby):
    result = fw.send_command(cmd)
    if result:
        print(result)
    else:
        print(fw.errors)

pass
