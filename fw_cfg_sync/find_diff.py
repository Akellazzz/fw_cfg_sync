""" Сравнение двух конфигураций Cisco ASA

Пример: 

find_diff.py test1_2022-01-28_17-01-35.txt test1_2022-01-25_18-51-21.txt

Результат:

Команды только в test1_2022-01-28_17-01-35.txt
object network on22
 host 1.1.1.1
object network on17
 host 1.1.1.1

В файле 2 нет уникальных команд

"""

###
###
### TODO упорядочить вывод
###

import time

from functions.find_delta import find_delta
import sys

file1 = str(sys.argv[1])
file2 = str(sys.argv[2])
uniq_in_file1, uniq_in_file2 = find_delta(file1, file1, file2, file2)
time.sleep(1)
if uniq_in_file1:
    print(f"Команды только в {file1}")
    print(f"{uniq_in_file1}")
else:
    print(f"В файле {file1} нет уникальных команд")
if uniq_in_file2:
    print(f"Команды только в {file2}")
    print(f"{uniq_in_file2}")
else:
    print(f"В файле {file2} нет уникальных команд")
