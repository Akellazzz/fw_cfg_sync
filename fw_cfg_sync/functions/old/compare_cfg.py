from ..create_cfg_for_standby import config_parser, config_parser_sum
from ..helpers import PARSE_DICT
from ciscoconfparse import CiscoConfParse

# from variables import *


def print_result_simple(result):
    for block in PARSE_DICT:
        act = result["active"][block]
        bak = result["backup"][block]
        if act == bak:
            print(f"{block:<20} OK")
        else:
            print(f"{block:<20} FAIL")
            diff = act ^ bak
            if diff:
                file1_only = act.difference(bak)
                file2_only = bak.difference(act)

                if file1_only:
                    print("---- Только в active:")
                    file1_out = str()
                    for i in list(file1_only):
                        file1_out += "\n".join(i)
                        file1_out += "\n!\n"
                    print(file1_out)
                if file2_only:
                    print("---- Только в backup:")
                    file2_out = str()
                    for i in list(file2_only):
                        file2_out += "\n".join(i)
                        file2_out += "\n!\n"
                    print(file2_out)


def compare_cfg(file1, file2):
    if config_parser_sum(file1) == config_parser_sum(file2):
        return True


def show_diff(name1, file1, name2, file2, datetime_now):
    with open(file1, "r") as f1, open(file2, "r") as f2:
        parse1 = CiscoConfParse(f1.readlines())
        parse2 = CiscoConfParse(f2.readlines())
    for block, template in PARSE_DICT.items():
        res = []
        res1 = set(tuple(i.ioscfg) for i in config_parser(parse1, template))
        res2 = set(tuple(i.ioscfg) for i in config_parser(parse2, template))
        if res1 == res2:
            print(f"{block:<20} OK")
        else:
            print(f"{block:<20} FAIL")
            diff = res1 ^ res2
            if diff:
                file1_only = res1.difference(res2)
                file2_only = res2.difference(res1)

                if file1_only:
                    print(f"---- Только в {name1}:")
                    file1_out = str()
                    for i in list(file1_only):
                        file1_out += "".join(i)
                        # file1_out += "!"
                    print(file1_out)
                if file2_only:
                    print(f"---- Только в {name2}:")
                    file2_out = str()
                    for i in list(file2_only):
                        file2_out += "".join(i)
                        # file2_out += "!"
                    print(file2_out)


# def print_result(result):
#     for block in PARSE_DICT:

#         if block in ["name", "object-group", "flow-export", "nat", "service-policy", "object_not_for_nat", "object_for_nat", "class-map", "policy-map"]:
#             if result["active"][block] == result["backup"][block]:
#                 print(f"{block:<20} OK")
#             else:
#                 print(f"{block:<20} FAIL")
#                 diff = result["active"][block] ^ result["backup"][block]
#                 print(diff)

#         if block == "time-range":
#             empty_tr_a, not_empty_tr_a = analize_tr(result["active"]["time-range"])
#             empty_tr_b, not_empty_tr_b = analize_tr(result["backup"]["time-range"])
#             assert bool(set(empty_tr_a) & set(not_empty_tr_a)) == False
#             assert bool(set(empty_tr_b) & set(not_empty_tr_b)) == False

#         if block == "access-list":
#             missed_acl = []
#             acl_list_active = [x[0].strip() for x in result["active"]["access-list"]]
#             acl_list_backup = [x[0].strip() for x in result["backup"]["access-list"]]

#             acl_with_cutted_empty_tr_active = cut_empty_tr(acl_list_active, empty_tr_a)
#             acl_with_cutted_empty_tr_backup = cut_empty_tr(acl_list_backup, empty_tr_b)

#             for i in acl_list_active:
#                 if i in (acl_list_backup + acl_with_cutted_empty_tr_backup):
#                     continue

#                 else:
#                     print(i) #TODO

#             for i in acl_list_backup:
#                 if i in (acl_list_active + acl_with_cutted_empty_tr_active + acl_with_cutted_empty_tr_backup):
#                     continue

#                 else:
#                     # print(i)

#                     if " time-range " in i:
#                         acl_wo_tr = i.split(" time-range ")[0].strip()
#                         tr = i.split(" time-range ")[-1].strip()
#                         if tr in empty_tr_b and acl_wo_tr in acl_list_active:
#                             continue

#                         else:
#                             missed_acl.append(i)
#                             print(i) #TODO

#                     else:
#                         missed_acl.append(i)
#                         print(i) #TODO
#             # print(missed_acl)
#             pass
