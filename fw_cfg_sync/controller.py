from functions.check_prereq import check_prereq
from functions.backup_cfg import backup_cfg
from functions.create_cfg_for_standby import create_cfg_for_standby
from functions.deploy_cfg_to_standby import deploy_cfg_to_standby
from functions.compare_cfg import compare_cfg


if __name__ == "__main__":

    # check_prereq()

    backup_cfg()

    create_cfg_for_standby()

    deploy_cfg_to_standby()

    # compare_cfg()
