from datetime import datetime
from netmiko import ConnectHandler

import os
import sys
import logging

logging.basicConfig(filename="fw_cfg_sync/logs/netmiko.log", level=logging.DEBUG)
logger = logging.getLogger("netmiko")


class BaseConnection:
    def __init__(self, **kwargs):
        # self.__dict__.update(kwargs)
        self.name = kwargs.get("name") if kwargs.get("name") else kwargs.get("conn").get("host")
        self.conn = kwargs.get("conn")
        self.conn["allow_auto_change"] = False
        self.errors = []

    def send_command(self, command: str):
        try:
            with ConnectHandler(**self.conn) as net_connect:
                return net_connect.send_command(command) 
        except Exception as e:
            self.errors.append(e)

    def send_cfg_from_file(self, cfg_file: str):
        try:
            with ConnectHandler(**self.conn) as net_connect:
                r = net_connect.send_config_from_file(cfg_file) 
        except Exception as e:
            self.errors.append(e)
        return r


class Multicontext(BaseConnection):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.__dict__.update(kwargs)
        self.contexts = []

    def get_contexts(self):
        contexts = []
        with ConnectHandler(**self.conn) as net_connect:
            net_connect.send_command(f"changeto system") 
            r = net_connect.send_command("show context | in Routed")
        lines = r.split("\n")
        for line in lines:
            line = line.strip()
            if not line.startswith("*"):
                context = line.split()[0]
                contexts.append(context)   
        self.contexts = dict.fromkeys(contexts)

    def send_command_to_context(self, command: str, context: str = ""):
        try:
            with ConnectHandler(**self.conn) as net_connect:
                if context:
                    net_connect.send_command(f"changeto context {context}") 
                return net_connect.send_command(command) 
        except Exception as e:
            self.errors.append(e)

    def get_context_backup(self, context):
        ''' Забирает бэкап конфигурации контекста и сохраняет в self.contexts[context]['config']
        Если хост недоступен, сохраняет ошибку в self.contexts[context]['errors']'''
        result = self.send_command_to_context(command = "show run", context = context)
        if result and result.endswith(": end"):
            self.contexts[context] = result
        else:
            print(f"Unable to get config from {context}")
            self.errors.append(result)
            self.contexts[context]['errors']

    def save_run_cfg_locally(self, context):
        ''' Сохраняет бэкап конфигурации в файл {имя_МСЭ}_{контекст}_{время}.txt'''
        d = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # dirname = os.path.join(os.path.dirname(__file__), "fw_configs") 
        filename = self.name + '_' + context + '_' + d + '.txt'
        # full_path = os.path.join(dirname, filename) 
        main_dir = os.path.dirname(sys.argv[0]) # путь к главной директории 
        full_path = os.path.join(main_dir, "fw_configs", filename) 
        with open(full_path, "w") as f:
            f.write(self.contexts[context])

