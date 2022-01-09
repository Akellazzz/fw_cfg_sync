from ciscoconfparse import CiscoConfParse
import yaml

PARSE_DICT = {
    # шаблоны поиска для КЕ
    "names": r"^names$",
    "no_names": r"^no\snames$",
    "name": r"^name\s",
    "object_not_for_nat": {
        "parentspec": r"^object\s",
        "childspec": r"^\snat\s",
        "find_obj_mode": "without",
    },
    "object_for_nat": {
        "parentspec": r"^object\s",
        "childspec": r"^\snat\s",
        "find_obj_mode": "with",
    },
    "object-group": r"^object-group\s",
    "time-range": r"^time-range\s",
    "access-list": r"^access-list\s",
    "class-map": r"^class-map\s",
    "flow-export": r"^flow-export\s",
    "policy-map": r"^policy-map\s",
    "service-policy": r"^service-policy\s",
    "access-group": r"^access-group\s",
    "nat": r"^nat\s",
}

CLEAR_COMMANDS = [
    "clear configure service-policy",
    "clear configure policy-map",
    "clear configure class-map",
    "clear configure flow-export",
    "clear configure nat",
    "clear configure access-list",
    "clear configure object-group",
    "clear configure object",
    "clear configure time-range",
    "clear configure access-group",
    "clear configure name",
    "clear configure names",
]


# def init_config(file):
#     with open(file, "r") as stream:
#         try:
#             init_config = yaml.safe_load(stream)
#         except yaml.YAMLError as exc:
#             print(exc)
#     active = init_config[0].get("dev").get("active")
#     standby = init_config[0].get("dev").get("standby")
#     return active, standby


def erase_file(fullpath):
    # erase file
    open(fullpath, "w").close()
