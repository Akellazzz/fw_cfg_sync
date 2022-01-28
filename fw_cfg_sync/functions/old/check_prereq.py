import sys

from variables import *
from functions.connection import add_connection_args
from functions.connection import send_commands


def _check_description(
    host=SYSTEM_CONTEXT,
    auth_username=USERNAME,
    auth_password=PASSWORD,
):
    device = add_connection_args(host, auth_username, auth_password)
    result = send_commands(device, CONTEXT_COMMANDS)
    if DESCRIPTION in result.result:
        return True  # TODO посмотреть как это сделано в текущем скрипте (какие указываются входные аргументы)


def _check_route(
    host=SWITCH,
    auth_username=USERNAME,
    auth_password=PASSWORD,
    show_route_cmd=SHOW_ROUTE_CMD,
    route=ROUTE,
):
    device = add_connection_args(host, auth_username, auth_password)
    result = send_commands(device, [show_route_cmd])
    if result:
        if route in result.result:
            return True


def check_prereq():

    if IS_CONTEXT:
        description_found = _check_description()
        if not description_found:
            print("description not found")
            sys.exit()

    route_found = _check_route()
    if route_found:
        print("route found")
    else:
        print("route not found")
        sys.exit()
