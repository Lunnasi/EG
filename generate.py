import names
import random
import csv


a = b = 0
count = 1000000

csv.register_dialect('myDialect',
delimiter = ';',
quoting=csv.QUOTE_NONE,
skipinitialspace=True)


def count_rows(n):
  while n != 0:
    yield (names.get_first_name() ,names.get_last_name(), random.randint(10, 80))
    n -= 1

for x in range(count):
  row = count_rows(count)
  if a % 100000 == 0:
    b = a % 100000
    print(str(b + " %" + " is done")
  with open('./generated_values/person_'+ str(b) +'.txt', 'a+') as f:
    writer = csv.writer(f, dialect='myDialect', lineterminator ='\r')
    writer.writerow(next(row))
  f.close()
  a += 1