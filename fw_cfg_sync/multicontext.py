import logging
from scrapli.driver import GenericDriver

logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)
logger = logging.getLogger("scrapli")


def disable_paging(conn):
    conn.send_interactive(
        [("enable", "assword:"), (conn.auth_password, "#", True),]
    )
    conn.channel.send_input("terminal pager 0")
    conn.channel.send_input("terminal width 500")


def get_contexts(device):
    contexts = []
    conn = GenericDriver(**device)
    try:
        conn.open()
        conn.send_command("changeto system")
        r = conn.send_command("show context | in Routed").result
        # conn.transport.close()
        lines = r.split("\n")
        for line in lines:
            line = line.strip()
            if not line.startswith("*"):
                context = line.split()[0]
                contexts.append(context)   
        print(contexts)
        conn.close()
    except:
        pass
    return contexts

def get_context_backup(device, context):
    conn = GenericDriver(**device)
    try:
        conn.open()
        conn.send_command(f"changeto context {context}")
        result = conn.send_command("show run").result
        print(r)
        conn.close()
    except:
        pass
    return result


device = {
    "host": "192.168.89.115",
    "auth_username": "aaa",
    "auth_password": "aaa",
    "auth_strict_key": False,
    "on_open": disable_paging,
    "transport": "ssh2",

    # "transport_options": {"open_cmd": all_fw[fw]["transport_options"]},
}
contexts = get_contexts(device)
if not contexts:
    #TODO
    pass
for context in contexts:
    backup = get_context_backup(device, context)
    print(backup)
    
# print(get_contexts(device))
pass