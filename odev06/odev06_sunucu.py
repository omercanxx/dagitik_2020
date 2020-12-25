import socket
import sys
import threading
import queue
import time
from datetime import datetime

class rThread(threading.Thread):
    def __init__(self, threadID, conn, c_addr, qThread, qLog,uDict, isEntered, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.conn = conn
        self.c_addr = c_addr
        self.qThread = qThread
        self.qLog = qLog
        self.uDict = uDict
        self.isEntered = isEntered
        self.name = name

    def run(self):
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            self.conn.sendall(current_time.encode('utf-8'))
            data = self.conn.recv(1024)
            data_str = data.decode().strip()
            print("%s : %s" %(self.c_addr, data_str))
            self.incoming_parser(data_str, current_time)
        self.conn.close()
        print("Thread %s kapanıyor" % self.threadID)

    def incoming_parser(self, data, time):
        #Kullanıcı ismi kontrolu için
        
        msg = data.strip().split(" ")
        if msg[0] == "NIC":
            #and self.isEntered == false ile aynı makineden aynı anda birden fazla girişi engelleniyor.
            if msg[1] not in self.uDict.keys() and self.isEntered == False:
                self.name = msg[1]
                self.uDict[self.name] = self.qThread
                self.isEntered = True
                self.qThread.put("WEL\n")
                self.qLog.put("<"+time+"> " +"WEL " + "from server to " + self.name +"\n")
            else:
                self.qThread.put("REJ\n")
                self.qLog.put("<"+time+"> " +"REJ " + "from server to " + self.name +"\n")

        elif msg[0] == "QUI" and self.isEntered:
            self.qThread.put("BYE"+" "+self.name)
            self.qLog.put("<"+time+"> " +"BYE " + "from server to " + self.name +"\n")
            del self.uDict[self.name]
            self.conn.close()

        elif msg[0] == "QUI" and self.isEntered == False:
            self.qThread.put("BYE")
            self.conn.close()
            self.qLog.put("<"+time+"> " + "BYE " + "from server to unnamed user\n")
        elif msg[0] == "GLS" and self.isEntered:
            userList = []
            for key in self.uDict.keys():
                userList.append(key)
            print(":".join(userList))
            lst = "LST"+ " "+ ":".join(userList)
            self.qThread.put(lst)
            self.qLog.put("<"+time+"> "+lst + " from server to " + self.name +"\n")

        elif msg[0] == "GNL" and self.isEntered:
            seperator = " "
            msg = seperator.join(msg[1:])
            gnlmsg = "GNL"+ " "+ self.name+ ":" + msg + "\n"
            for value in self.uDict.values():
                value.put(gnlmsg)
            self.qLog.put("<"+time+"> " +msg + " from " + self.name + " to everyone\n")
        elif msg[0] == "PRV" and self.isEntered:
            isOnline = False
            prvmsg = msg[1].split(":")

            for key in self.uDict.keys():
                if key == prvmsg[0]:
                    q = self.uDict.get(prvmsg[0])
                    isOnline = True

            if isOnline == True:
                q.put("PRV" + " "+ self.name+ ":"+ prvmsg[1])
                self.qLog.put("<"+time+"> " +prvmsg[1] + " from " + self.name +" to " + prvmsg[0] +"\n")

            else :
                self.qThread.put("NOP"+ " "+ prvmsg[0])
                self.qLog.put("<"+time+"> " +"NOP " + "from server to " + self.name +"\n")                
        elif self.isEntered == False:
            self.qThread.put("LRR")
            self.qLog.put("<"+time+"> " +"LRR " + "from server to unnamed user\n")

        elif msg[0] in ["TON", "ERR", "OKG", "OKP"]:
            pass

        else:
            self.qThread.put("ERR")
            self.qLog.put("<"+time+"> " +"ERR " + "from server to " + self.name + "\n")

class wThread(threading.Thread):
    def __init__(self, tName, conn, qThread):
        threading.Thread.__init__(self)
        self.conn = conn
        self.qThread = qThread
        self.tName = tName

    def run(self):
        print(self.tName, "Starting.")

        while True:
            data = self.qThread.get()
            self.conn.send(data.encode())
        print(self.tName, "Exiting.")

class lThread(threading.Thread):
    def __init__(self, tName, q):
        threading.Thread.__init__(self)
        self.tName = tName
        self.q = q
    def run(self):
        print(self.tName, "Starting.")

        while True:
            file = open('log.txt', 'a+')
            data = self.q.get()
            print(data)
            file.write(data)
            file.close()

def main():
    
    server_socket = socket.socket()
    queueEmpty = queue.Queue

    #Kullanıcı giriş kontrolü
    userDict = {}
    isEntered = False
    name = ""

    ip = "0.0.0.0"
    port = int(sys.argv[1])
    addr_server = (ip, port)

    server_socket.bind(addr_server)
    server_socket.listen(5)

    counter = 0
    threads = []
    
    #loglama işlemi için
    
    queueLog = queue.Queue()
    logThread = lThread("LogThread", queueLog)
    logThread.start()
    
    while True:

        queueThread = queue.Queue()
        conn, addr = server_socket.accept()
        readThread = rThread(counter, conn, addr, queueThread, queueLog, userDict, isEntered, name)
        writeThread = wThread("WriteThread", conn, queueThread)

        readThread.start()
        writeThread.start()
    server_socket.close()


if __name__ == "__main__":
    main()