import pytest
import os
import sys
from pathlib import Path
# sys.path.insert(0, str(Path.cwd() / '..' / '..'))
sys.path.insert(0, str(Path(__file__) / '..' / '..' / '..'))
# breakpoint()
from show_diff import without_empty_tr

def test_without_empty_tr():
# goal_dir = os.path.join(os.getcwd(), "../..")


    file1 = os.path.join(
        pytest.tests_dir, "fw_configs_for_tests", "with_empty_tr1.txt"
    )
    file2 = os.path.join(
        pytest.tests_dir, "fw_configs_for_tests", "with_empty_tr2.txt"
    )

    uniq_in_file1, uniq_in_file2 = without_empty_tr(file1, file2)
    breakpoint()
    assert uniq_in_file1 
    assert 'absolute end 00:00 16 December 2025_in_use1' in uniq_in_file1 
    assert 'time-range empty_tr_not_in_use1' not in uniq_in_file1 
    assert 'access-list test extended permit ip any any time-range empty_tr_in_use1' not in uniq_in_file1 
    assert 'access-list test extended permit ip any any time-range not_empty_tr_in_use1' in uniq_in_file1 

    assert uniq_in_file2 
    breakpoint()