'''Классы для взаимодействия с хостами.

BaseConnection - базовый класс
Multicontext - для взаимодействия с мультиконтекстными МСЭ Cisco ASA
'''
from datetime import datetime
from netmiko import ConnectHandler, NetmikoTimeoutException
from loguru import logger

import os
import sys
import logging

# logging.basicConfig(filename="fw_cfg_sync/logs/netmiko.log", level=logging.DEBUG)
# logger = logging.getLogger("netmiko")

# logger.configure(**log_config)

class BaseConnection:
    '''Базовый класс'''

    def __init__(self, **kwargs):
        # self.__dict__.update(kwargs)
        self.name = kwargs.get("name") if kwargs.get("name") else kwargs.get("conn").get("host")
        self.conn = kwargs.get("conn")
        self.is_reachable: bool
        self.conn["allow_auto_change"] = False
        

    @logger.catch
    def check_reachability(self):
        '''Проверка возможности подключения к устройству'''

        try:
            with ConnectHandler(**self.conn) as net_connect:
                self.is_reachable = True
                logger.debug(f'Подключение к устройству {self.name} успешно')

        except NetmikoTimeoutException as e:
            self.is_reachable = False
            logger.error(f'TCP connection to {self.name} failed')
            

    @logger.catch
    def send_command(self, command: str):
        logger.debug(f'Отправка команды {command} устройству {self.name}')

        try:
            with ConnectHandler(**self.conn) as net_connect:
                return net_connect.send_command(command) 
        except NetmikoTimeoutException as e:
            logger.error(f'TCP connection to {self.name} failed')


    @logger.catch
    def send_cfg_from_file(self, cfg_file: str):
        logger.debug(f'Отправка устройству {self.name} команд из файла {cfg_file}')
        try:
            with ConnectHandler(**self.conn) as net_connect:
                return net_connect.send_config_from_file(cfg_file) 
        except NetmikoTimeoutException as e:
            logger.error(f'TCP connection to {self.name} failed')

class Multicontext(BaseConnection):
    '''Класс для взаимодействия с мультиконтекстными МСЭ Cisco ASA '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.__dict__.update(kwargs)
        self.contexts = []

    @logger.catch
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


    @logger.catch
    def send_command_to_context(self, command: str, context: str = ""):
        try:
            with ConnectHandler(**self.conn) as net_connect:
                if context:
                    net_connect.send_command(f"changeto context {context}") 
                return net_connect.send_command(command) 
        except NetmikoTimeoutException as e:
            logger.error(f'TCP connection to {self.name} failed')


    def get_context_backup(self, context):
        ''' Забирает бэкап конфигурации контекста и сохраняет в self.contexts[context]['config']'''

        result = self.send_command_to_context(command = "show run", context = context)
        if result and result.endswith(": end"):
            self.contexts[context] = result
        else:
            logger.error(f'Unable to get config from {self.name} - {context}')


    def save_backup_to_file(self, context):
        ''' Сохраняет бэкап конфигурации в файл {имя_МСЭ}_{контекст}_{время}.txt'''

        d = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # dirname = os.path.join(os.path.dirname(__file__), "fw_configs") 
        filename = self.name + '_' + context + '_' + d + '.txt'
        # full_path = os.path.join(dirname, filename) 
        main_dir = os.path.dirname(sys.argv[0]) # путь к главной директории 
        full_path = os.path.join(main_dir, "fw_configs", filename) 
        with open(full_path, "w") as f:
            f.write(self.contexts[context])

