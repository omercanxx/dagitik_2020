import sys
import collections

numberRepetition = int(sys.argv[1])
personDictionary = {}
personTuple = ()

for i in range(numberRepetition):
    answers = input("ID Name Surname Age\n")
    if len(answers.split()) == 5:
        answers_split = answers.split()
        idNumber = int(answers_split[0])
        if idNumber not in personDictionary.keys():
            name = str(" ".join(answers_split[1:3]))
            surname = str(answers_split[3])
            age = int(answers_split[4])

            person = (name, surname, age)
            personDictionary[idNumber] = person

        else:
            print("Already registered person")

    elif len(answers.split()) == 4:
        answers_split = answers.split()
        idNumber = int(answers_split[0])
        if idNumber not in personDictionary.keys():
            name = str(answers_split[1])
            surname = str(answers_split[2])
            age = int(answers_split[3])

            person = (name, surname, age)
            personDictionary[idNumber] = person

        else:
            print("Already registered ID")
    else:
        print("Error")

personTuple = personDictionary.values()

od = collections.OrderedDict(sorted(personDictionary.items()))
print(od.values())

