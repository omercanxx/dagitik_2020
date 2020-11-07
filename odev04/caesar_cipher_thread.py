import queue
import threading
import sys

class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print("Starting " + self.name)
        shifting(self.name, qPlain, qCrypted, s)
        print("Exiting " + self.name)


def process_data(q):
    while not q.empty():
        print(q.get())

def shifting(threadName, qP, qC, s):
    while True:
        queueLock.acquire()
        if not qP.empty():
            result = ""
            text = qP.get()
        # traverse text
            for i in range(len(text)):
                char = text[i]
            # Encrypt uppercase characters
                if (char.isupper()):
                    result += chr((ord(char) + s - 65) % 26 + 65)
                # Encrypt lowercase characters
                elif(char.islower()):
                    result += chr((ord(char) + s - 97) % 26 + 97)
                else:
                    result += char
            if(result == ''):
                break
            file2.write(result)
            qC.put(result)
            #process_data(qC)
            queueLock.release()


name = 'crypted_thread_15_14_40'
processes = []
qPlain = queue.Queue()
qCrypted = queue.Queue()
queueLock = threading.Lock()
file2 = open("%s.txt" % name, "w")

s = int(sys.argv[1])
l = int(sys.argv[2])
n = int(sys.argv[3])

with open("input.txt") as file:
    for line in file:
        for five_character in line:
            five_character = file.read(l)
            qPlain.put(five_character)



for i in range(n):
    p = myThread(i, "Thread-%s" % i, i)
    processes.append(p)
    p.start()

for p in processes:
    p.join()

print("Exiting Main Thread")

file.close()
file2.close()