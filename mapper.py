#!/usr/bin/env python3
"""mapper.py"""
from clickhouse_driver import Client
import sys

currentName = None
client = Client('192.168.56.14')

client.execute('CREATE DATABASE IF NOT EXISTS mr_db')
client.execute('CREATE TABLE IF NOT EXISTS mr_db.task3 (name String, surname String, age String) ENGINE=File(TabSeparated)')
# input comes from STDIN (standard input)

for line in sys.stdin:
        line = line.strip()
        line = line.split(',', 2)
        name = line[0].rstrip()
        surname = line[1].rstrip()
        age = line[2].rstrip()
#        print(name,surname,age)
        client.execute('INSERT INTO mr_db.task3 VALUES',[[name,surname,age]])
