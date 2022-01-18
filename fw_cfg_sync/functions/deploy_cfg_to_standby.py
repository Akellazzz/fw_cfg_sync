from .backup_cfg import save_run_cfg_locally

from .connection import send_config_from_file
from .helpers import CLEAR_COMMANDS
import sys


def clear_config(device, file):
    result = send_config_from_file(device, file)
    if result == None:
        print("Unable to clear config")
        sys.exit()

    elif result.failed:
        print("Unable to clear config")
        sys.exit()

    # TODO проверить, что конфиг очищен


def _configure_standby(device, filename):
    result = send_config_from_file(device, filename)
    return result


def _check_cfg_cleared(device):
    pass  # TODO


def deploy_cfg_to_standby(
    host, config_for_standby_test_file, new_standby_cfg, clear_config_commands_file
):
    # standby = add_connection_args(
    #     host.get("ip"), host.get("username"), host.get("password")
    # )
    standby = host
    # import pdb
    # pdb.set_trace()
    clear_config(standby, clear_config_commands_file)
    _check_cfg_cleared(standby)
    _configure_standby(standby, config_for_standby_test_file)

    save_run_cfg_locally(standby, new_standby_cfg)
