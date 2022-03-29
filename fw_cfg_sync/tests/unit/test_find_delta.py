from ciscoconfparse import CiscoConfParse
from ...functions.find_delta import block_parser, find_delta
import os
import pytest


def test_block_parser():
    with open(
        os.path.join(pytest.tests_dir, "fw_configs_for_tests", "active_cfg_file.txt")
    ) as f:
        parse = CiscoConfParse(f.readlines())

    x = block_parser(parse, r"^policy-map\s")
    assert "policy-map" in x[0].ioscfg[0]


def test_find_delta():
    """
    Одинаковые файлы
    """
    file1 = os.path.join(
        pytest.tests_dir, "fw_configs_for_tests", "active_cfg_file.txt"
    )
    file2 = os.path.join(
        pytest.tests_dir, "fw_configs_for_tests", "active_cfg_file.txt"
    )

    file1_uniq, file2_uniq = find_delta(file1, file2)
    assert file1_uniq == file2_uniq


def test_empty_backup():
    """
    Пустой файл
    """
    file1 = os.path.join(
        pytest.tests_dir, "fw_configs_for_tests", "active_cfg_file.txt"
    )
    file2 = os.path.join(pytest.tests_dir, "fw_configs_for_tests", "empty.txt")
    assert find_delta(file1, file2)[0] != ""
    assert find_delta(file1, file2)[1] == ""


def test_acl_order():
    """
    Порядок ACL
    """
    file1 = os.path.join(
        pytest.tests_dir, "fw_configs_for_tests", "active_cfg_file.txt"
    )
    file2 = os.path.join(pytest.tests_dir, "fw_configs_for_tests", "empty.txt")

    file1_uniq, _ = find_delta(file1, file2)
    list_ = file1_uniq.split("\n")
    acl = [i.strip() for i in list_ if i.startswith("access-list")]
    first = "access-list test extended permit ip any any time-range tr49"
    second = "access-list test extended permit icmp any any time-range tr49"
    third = "access-list acl_og0 extended deny ip object-group og0 host 8.8.8.8"
    # breakpoint()
    assert acl.index(first) < acl.index(second) < acl.index(third)


def test_acl_order2():
    """
    Сравнение
    """
    file1 = os.path.join(
        pytest.tests_dir, "fw_configs_for_tests", "active_cfg_file.txt"
    )
    file2 = os.path.join(
        pytest.tests_dir, "fw_configs_for_tests", "active_cfg_file_changed.txt"
    )
    file1_uniq, file2_uniq = find_delta(file1, file2)

    # Одинаковые
    assert "service-policy global_policy global" not in file1_uniq, file2_uniq

    # Дельта
    file1_uniq_list = file1_uniq.strip().split("\n")
    file2_uniq_list = file2_uniq.strip().split("\n")
    # breakpoint()
    assert file1_uniq_list == [
        "object network on0",
        " host 1.1.1.1",
        "object network on1",
        " host 1.1.1.1",
        "object-group network og0",
        " network-object host 1.1.1.1",
        " network-object 10.1.1.0 255.255.255.0",
        "object-group network og1",
        " network-object host 1.1.1.1",
        " network-object 10.1.1.0 255.255.255.0",
        "object-group protocol obj_prot0",
        " description test_og_prot",
        " protocol-object icmp",
        "object-group protocol obj_prot1",
        " description test_og_prot",
        " protocol-object icmp",
        "time-range tr0",
        " absolute end 00:00 16 December 2025",
        "time-range tr1",
        " absolute end 00:00 16 December 2025",
        "access-list test extended permit ip any any time-range tr49 ",
        "access-list test extended permit icmp any any time-range tr49",
        # "policy-map type inspect dns migrated_dns_map_1",
        # " parameters",
        # "  message-length maximum client auto",
        # "  message-length maximum 512",
    ]

    assert file2_uniq_list == [
        "object network on0_diff",
        " host 1.1.1.1",
        "object network on1_diff",
        " host 1.1.1.1",
        "object-group network og0_diff",
        " network-object host 1.1.1.1",
        " network-object 10.1.1.0 255.255.255.0",
        "object-group network og1_diff",
        " network-object host 1.1.1.1",
        " network-object 10.1.1.0 255.255.255.0",
        "object-group protocol obj_prot0_diff",
        " description test_og_prot",
        " protocol-object icmp",
        "object-group protocol obj_prot1_diff",
        " description test_og_prot",
        " protocol-object icmp",
        "time-range tr0_diff",
        " absolute end 00:00 16 December 2025",
        "time-range tr1_diff",
        " absolute end 00:00 16 December 2025",
        "access-list test extended permit ip any any time-range tr49_diff ",
        "access-list test extended permit icmp any any time-range tr49_diff",
        # "policy-map type inspect dns migrated_dns_map_1",
        # " parameters",
        # "  message-length maximum client auto_diff",
        # "  message-length maximum 512",
        # "policy-map global_policy_diff",
        # " class inspection_default",
        # "  inspect dns migrated_dns_map_1 ",
        # "  inspect ftp ",
        # "policy-map global_policy",
        # " class inspection_default",
        # "  inspect dns migrated_dns_map_1_diff",
        # "  inspect ftp",
    ]

    """
    отличающийся child
    """
    # assert "message-length maximum client auto_diff" not in file1_uniq
    # assert "message-length maximum client auto_diff" in file2_uniq
