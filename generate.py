import names
import random
import csv

person = []

a = b = 0

csv.register_dialect('myDialect',
delimiter = ';',
quoting=csv.QUOTE_NONE,
skipinitialspace=True)

for x in range(1000000):
  person.append([names.get_first_name(), names.get_last_name(), random.randint(10, 80)])
  a += 1
  if a == 10000:
      b = b + 1
      print(str(b)+" %")
      a = 0 
      if b % 10 == 0:
        with open('./generated_values/person_'+ str(b) +'.csv', 'a+') as f:
            writer = csv.writer(f, dialect='myDialect', lineterminator ='\r')
            for row in person: writer.writerow(row)
        f.close()