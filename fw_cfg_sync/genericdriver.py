# с чистым скрапли и с комьюнити дев возвращает только кусок конфига, при этом через cisco_asa отдает весь, но лезет в conf t

# DEBUG:scrapli.channel:read: b'asa-active# '
# INFO:scrapli.driver:connection to '192.168.89.111' on port '22' opened successfully
# INFO:scrapli.channel:sending channel input: sh run; strip_prompt: True; eager: False
# DEBUG:scrapli.channel:write: 'sh run'
# DEBUG:scrapli.channel:read: b's'
# DEBUG:scrapli.channel:read: b'h'
# DEBUG:scrapli.channel:read: b' '
# DEBUG:scrapli.channel:read: b'r'
# DEBUG:scrapli.channel:read: b'u'
# DEBUG:scrapli.channel:read: b'n'
# DEBUG:scrapli.channel:write: '\n'
# DEBUG:scrapli.channel:read: b'\n'
# DEBUG:scrapli.channel:read: b': Saved\n'
# DEBUG:scrapli.channel:read: b': \n'
# INFO:scrapli.driver:closing connection to '192.168.89.111' on port '22'
# DEBUG:scrapli.transport:closing transport connection to '192.168.89.111' on port '22'
# DEBUG:scrapli.socket:closing socket connection to '192.168.89.111' on port '22'
# DEBUG:scrapli.socket:closed socket connection to '192.168.89.111' on port '22' successfully
# DEBUG:scrapli.transport:transport connection to '192.168.89.111' on port '22' closed successfully
# INFO:scrapli.driver:connection to '192.168.89.111' on port '22' closed successfully


from scrapli.driver import GenericDriver
from scrapli import Scrapli
import os
import logging

log_file = os.path.dirname(__file__) + f"/logs/scrapli.log"

logging.basicConfig(filename=log_file, level=logging.DEBUG)

def disable_paging(conn):
    conn.send_interactive(
        [("enable", "assword:"), (conn.auth_password, "#", True),]
    )
    conn.channel.send_input("terminal pager 0")
    conn.channel.send_input("terminal width 500")

class BaseConnection:
    def __init__(self, **kwargs):
        # self.__dict__.update(kwargs)
        self.conn = kwargs.get("conn")
        self.errors = []
        self.on_open_commands = []

    def send_command(self, command: str):
        try:
            # conn = Scrapli(**self.conn)
            conn = GenericDriver(**self.conn)
            conn.open()
            # if self.conn.get("platform") == "cisco_asa":
            #     conn.channel.send_input("terminal pager 0")
            #     if self.is_context:
            #         conn.send_command(f"changeto context {self.context_name}")
            r = conn.send_command(command).result
            conn.close()
        except Exception as e:
            print("My Scrapli Exception")
            print(e)
            return None
        return r


    def send_commands(self, commands: list):
        try:
            conn = Scrapli(**self.conn)
            conn.open()
            # if self.conn.get("platform") == "cisco_asa":
            #     conn.channel.send_input("terminal pager 0")
            #     if self.is_context:
            #         conn.send_command(f"changeto context {self.context_name}")
            r = conn.send_commands(commands).result
            conn.close()
        except:
            return None
        return r

class Active(BaseConnection):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.__dict__.update(kwargs)
        self.conn = kwargs.get("conn")
        self.is_context = kwargs.get("is_context")
        self.context_name = kwargs.get("context_name")
        self.run_config = ""
        self.errors = []
        self.on_open_commands = []
    


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
    # "auth_secondary": "aaa",
    "auth_strict_key": False,
    "on_open": disable_paging,
    "transport": "ssh2",
    # "platform": "cisco_asa",
}

x = BaseConnection(conn = device, is_context = True, context_name = "test1")
pass