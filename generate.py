import names
import random
import csv

count = 100

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
  if x % 10 == 0:
    b = x / (count*0.01)
    print(str(b) + " %" + " is done")
  with open('person_'+ str(b) +'.csv', 'a+') as f:
    writer = csv.writer(f, dialect='myDialect', lineterminator ='\r')
    writer.writerow(next(row))
  f.close()