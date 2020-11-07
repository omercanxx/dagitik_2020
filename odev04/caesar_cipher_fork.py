from multiprocessing import Lock, Process, Queue, current_process
import sys

qPlain = Queue()
qCrypted = Queue()
s = int(sys.argv[1])
l = int(sys.argv[2])
n = int(sys.argv[3])
processes = []
with open("input.txt") as file:
    for line in file:
        for five_character in line:
            five_character = file.read(l)
            qPlain.put(five_character)
file2 = open("crypted_fork_13_10_48.txt", "w")




def process_data(q):
    while not q.empty():
        print(q.get())

def worker(qP, qC, l):
    while True:
        if not qP.empty():
            result = ""
            text = qP.get()
            # traverse text
            for i in range(len(text)):
                char = text[i]
                # Encrypt uppercase characters
                if (char.isupper()):
                    result += chr((ord(char) + l - 65) % 26 + 65)
                # Encrypt lowercase characters
                elif (char.islower()):
                    result += chr((ord(char) + l - 97) % 26 + 97)
                else:
                    result += char
            print(result)
            file2.write(result)
            if(result==''):
                break


def main():

    for x in range(n):
        lock = Lock()
        p = Process(target=worker, args=(qPlain, qCrypted, l))
        p.start()
        lock.release()
        processes.append(p)
        qPlain.put('STOP')

    for p in processes:
        p.join()

    qCrypted.put('STOP')

    for status in iter(qCrypted.get, 'STOP'):
        print(status)

    file2.close()
    file.close()

if __name__ == '__main__':
    main()

