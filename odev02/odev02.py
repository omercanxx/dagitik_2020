import sys

# argumanlari al
air1 = sys.argv[1]
air2 = sys.argv[2]

airlines_dictionary = {}

# dosya oku
with open('airlines.txt') as airlines:
    for line in airlines:
        a = line.split(",")
        a[-1] = a[-1].strip()
        airlines_dictionary[a[0]] = a[1:]
#yol var mi?
if air1 in airlines_dictionary.keys():
    i = 0
    print(air1)
    while True:
        print("-> {}".format(airlines_dictionary[air1][i]))
        if airlines_dictionary[air1][i] == air2:
            break
        i += 1
else:
    print("Yol yok!")