from scrapli.driver import GenericDriver
from scrapli import Scrapli
import os
import logging

log_file = os.path.dirname(__file__) + f"/logs/scrapli.log"

logging.basicConfig(filename=log_file, level=logging.DEBUG)

# def disable_paging(conn):
#     conn.send_interactive(
#         [("enable", "assword:"), (conn.auth_password, "#", True),]
#     )
#     conn.channel.send_input("terminal pager 0")
#     conn.channel.send_input("terminal width 500")

class AsaConnection:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.errors = []

    def send_command(self, command: str):
        try:
            conn = Scrapli(**self.conn)
            conn.open()
            if self.conn.get("platform") == "cisco_asa":
                conn.channel.send_input("terminal pager 0")

            r = conn.send_command(command).result
            conn.close()
        except:
            return None
        return r


    def send_commands(self, commands: list):
        try:
            conn = Scrapli(**self.conn)
            conn.open()
            if self.conn.get("platform") == "cisco_asa":
                conn.channel.send_input("terminal pager 0")

            r = conn.send_commands(commands).result
            conn.close()
        except:
            return None
        return r



    # def send_commands(self, commands: list):
    #     try:
    #         conn = GenericDriver(**self.conn)
    #         conn.open()
    #         r = conn.send_commands(commands).result
    #         conn.close()
    #     except:
    #         return None
    #     return r


# device = {
#     "host": "192.168.89.111",
#     "auth_username": "aaa",
#     "auth_password": "aaa",
#     "auth_strict_key": False,
#     "on_open": disable_paging,
#     "transport": "ssh2",
# }
# y = BaseConnection(conn = device)

device = {
    "host": "192.168.89.111",
    "auth_username": "aaa",
    "auth_password": "aaa",
    "auth_secondary": "aaa",
    "auth_strict_key": False,
    # "on_open": disable_paging,
    "transport": "ssh2",
    "platform": "cisco_asa",
}

x = AsaConnection(conn = device)
pass