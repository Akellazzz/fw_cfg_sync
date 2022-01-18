import platform

if platform.system() == "Windows":
    dirname = "C:\\Users\\eekosyanenko\\Documents\\poetry-fw_cfg_sync\\poetry_fw_cfg_sync\\tests\\"
    path_to_test_inventory = "C:\\Users\\eekosyanenko\\Documents\\poetry-fw_cfg_sync\\poetry_fw_cfg_sync\\tests\\"
    path_to_functions = "C:\\Users\\eekosyanenko\\Documents\\poetry-fw_cfg_sync\\poetry_fw_cfg_sync\\functions\\"
    path_to_test = "C:\\Users\\eekosyanenko\\Documents\\poetry-fw_cfg_sync\\poetry_fw_cfg_sync\\tests\\"
    path_to_test_configs = "C:\\Users\\eekosyanenko\\Documents\\poetry-fw_cfg_sync\\poetry_fw_cfg_sync\\tests\\fw_configs_for_tests\\"

elif platform.system() == "Linux":
    pass

INIT_TEST_CONFIG_FILE = path_to_test + "init_test_config.yaml"

active_cfg_file = path_to_test_configs + "active_cfg_file.txt"
active_cfg_file_backup = path_to_test_configs + "active_cfg_file_backup.txt"
changed_active_cfg_file = path_to_test_configs + "changed_active_cfg_file.txt"
clear_config_test_commands = path_to_test_configs + "clear_config_test_commands.txt"
config_for_standby_file = path_to_test_configs + "config_for_standby_file.txt"
config_for_standby_test_file = path_to_test_configs + "config_for_standby_test_file.txt"
fake_config = path_to_test_configs + "fake_config.txt"
fake_config_short = path_to_test_configs + "fake_config_short.txt"
new_standby_test_cfg = path_to_test_configs + "new_standby_test_cfg.txt"
standby_cfg_file_backup = path_to_test_configs + "standby_cfg_file_backup.txt"
