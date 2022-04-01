"""Классы для взаимодействия с хостами.

BaseConnection - базовый класс
Multicontext - для взаимодействия с мультиконтекстными МСЭ Cisco ASA
"""
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)
from loguru import logger

import os
import keyring
import sys
import logging

# logging.basicConfig(filename="fw_cfg_sync/logs/netmiko.log", level=logging.DEBUG)
# logger = logging.getLogger("netmiko")

# logger.configure(**log_config)


class BaseConnection:
    """Базовый класс"""

    # def __init__(self, **kwargs):
    # def __init__(self, name, host, username, fast_cli, enable_required, device_type, device_function):
    def __init__(self, name, host, credentials, fast_cli, enable_required, device_type, device_function, session_log = None):
        # self.__dict__.update(kwargs)
        self.conn = {}
        self.name = name
        self.device_function = device_function
        self.conn["host"] = host
        self.conn["device_type"] = device_type
        self.conn["username"] = keyring.get_credential(credentials, '').username
        self.conn["fast_cli"] = fast_cli
        self.conn["password"] = keyring.get_credential(credentials, '').password
        if enable_required:
            enable = keyring.get_credential(credentials + "_enable", '')
            if enable:
                self.conn["secret"] = enable.password
            else:
                logger.error(
                    f"enable password for {self.name} not found in saved system credentials: {credentials}_enable"
                )
                sys.exit()
        self.conn["allow_auto_change"] = False

        if session_log:
            self.conn["session_log"] = session_log
        self.is_reachable: bool

    @logger.catch
    def check_reachability(self):
        """Проверка возможности подключения к устройству"""

        try:
            with ConnectHandler(**self.conn) as net_connect:
                self.is_reachable = True
                logger.debug(f"Подключение к устройству {self.name} - успешно")

        except NetmikoTimeoutException as e:
            self.is_reachable = False
            logger.error(
                f"TCP connection to {self.name} failed (NetmikoTimeoutException)"
            )
            logger.debug(e)
        except NetmikoAuthenticationException as e:
            self.is_reachable = False
            logger.error(
                f"Authentication to {self.name} failed (NetmikoAuthenticationException)"
            )
            logger.debug(e)

    @logger.catch
    def send_command(self, command: str):
        logger.debug(f"Отправка команды {command} устройству {self.name}")

        try:
            with ConnectHandler(**self.conn) as net_connect:
                return net_connect.send_command(command)
        except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
            logger.error(f"{self.name} - {error}")

    @logger.catch
    def send_cfg_from_file(self, cfg_file: str):
        logger.debug(f"Отправка устройству {self.name} команд из файла {cfg_file}")
        try:
            with ConnectHandler(**self.conn) as net_connect:
                return net_connect.send_config_from_file(cfg_file)
        except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
            logger.error(f"{self.name} - {error}")


class Multicontext(BaseConnection):
    """Класс для взаимодействия с мультиконтекстными МСЭ Cisco ASA"""

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
        if contexts:
            logger.info(f"Сформирован список контекстов {self.name}: {contexts}")

            self.contexts = dict.fromkeys(contexts)
        else:
            logger.error(f"Не удалось сформировать список контекстов для {self.name}")

    @logger.catch
    def send_command_to_context(self, command: str, context: str = ""):
        try:
            with ConnectHandler(**self.conn) as net_connect:
                if context:
                    net_connect.send_command(f"changeto context {context}")
                return net_connect.send_command(command)
        except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
            logger.error(f"{self.name} - {error}")

    @logger.catch
    def get_context_backup(self, context, key="config"):
        """Забирает бэкап конфигурации контекста и сохраняет в self.contexts[context]['config']"""

        result = self.send_command_to_context(command="show run", context=context)
        if result and result.endswith(": end"):

            self.contexts[context][key] = result
            logger.info(
                f"С контекста {self.name}-{context} успешно считана конфигурация"
            )

        else:
            logger.error(f"Unable to get config from {self.name} - {context}")

    @logger.catch
    def save_backup_to_file(self, context, datetime_now):
        """Сохраняет бэкап конфигурации в файл {имя_МСЭ}_{контекст}_{время}.txt"""

        # d = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # dirname = os.path.join(os.path.dirname(__file__), "fw_configs")
        filename = f'{self.name}' + "-" + context + "_" + datetime_now + ".txt"
        # full_path = os.path.join(dirname, filename)
        # main_dir = os.path.dirname(sys.argv[0])  # путь к главной директории

        # путь к общей директории для сохранения бэкапов МСЭ
        parent_backup_dir = os.environ.get("FW-CFG-SYNC_BACKUPS")

        # путь к  директории для сохранения бэкапов контекстов
        backup_dir = os.path.join(parent_backup_dir, self.name)

        if not os.path.exists(backup_dir):
            os.mkdir(backup_dir)
            logger.info(f"Создана директория {backup_dir} ")

        # full_path = os.path.join(main_dir, "fw_configs", self.name,  filename)
        full_path = os.path.join(backup_dir, filename)
        self.contexts[context]["backup_path"] = full_path
        with open(full_path, "w") as f:
            f.write(self.contexts[context]["config"])
            logger.info(
                f"Конфигурация контекста {self.name}-{context} сохранена в файл {full_path}"
            )

    @logger.catch
    def send_config_set_to_context(self, config_set: list, context: str, datetime_now: str):
        filename = f'{self.name}-{context}_{datetime_now}_configuration_log.txt'

        # путь к общей директории для сохранения бэкапов МСЭ
        parent_backup_dir = os.environ.get("FW-CFG-SYNC_BACKUPS")

        # путь к директории для сохранения бэкапов контекстов
        backup_dir = os.path.join(parent_backup_dir, self.name)

        session_log_path = os.path.join(backup_dir, filename)
        self.contexts[context]["session_log_path"] = os.path.join(backup_dir, filename)

        # включение логирования
        self.conn['session_log'] = session_log_path
        
        try:
            with ConnectHandler(**self.conn) as net_connect:
                net_connect.send_command(f"changeto context {context}")
                net_connect.send_config_set(config_set, cmd_verify=False)

        except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
            logger.error(f"{self.name} - {error}")

        # выключение логирования
        self.conn.pop("session_log", None)
