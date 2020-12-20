import socket
import sys
import threading
import queue
from datetime import datetime

class rThread(threading.Thread):
    def __init__(self, threadID, conn, c_addr, qThread, uDict, isEntered, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.conn = conn
        self.c_addr = c_addr
        self.qThread = qThread
        self.uDict = uDict
        self.isEntered = isEntered
        self.name = name

    def run(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        self.conn.sendall(current_time.encode('utf-8'))
        
        while True:
            data = self.conn.recv(1024)
            data_str = data.decode().strip()
            print("%s : %s" %(self.c_addr, data_str))
            self.incoming_parser(data_str)
        self.conn.close()
        print("Thread %s kapanıyor" % self.threadID)

    def incoming_parser(self, data):
        #Kullanıcı ismi kontrolu için
        msg = data.strip().split(" ")
        if msg[0] == "NIC":
            #and self.isEntered == false ile aynı makineden aynı anda birden fazla girişi engelleniyor.
            if msg[1] not in self.uDict.keys() and self.isEntered == False:
                self.name = msg[1]
                self.uDict[self.name] = self.qThread
                self.isEntered = True
                self.qThread.put("WEL")
            else:
                self.qThread.put("REJ")
        elif msg[0] == "QUI" and self.isEntered:
            self.qThread.put("BYE")
        elif msg[0] == "GLS" and self.isEntered:
            self.qThread.put("LST ömer:ege:reşat:kıvanç")
        elif msg[0] == "PIN" and self.isEntered:
            self.qThread.put("PON")
        elif msg[0] == "GNL" and self.isEntered:
            seperator = " "
            msg = seperator.join(msg[1:])
            gnlmsg = "GNL"+ " "+ self.name+ ":" + msg
            for value in self.uDict.values():
                value.put(gnlmsg)
                value.put("OKG")
#            self.qThread.put(gnlmsg)
#            self.qThread.put("OKG")
        elif msg[0] == "PRV" and self.isEntered:
            isOnline = False
            prvmsg = msg[1].split(":")
            for key in self.uDict.keys():
                if key == prvmsg[0]:
                    q = self.uDict.get(prvmsg[0])
                    isOnline = True
            if isOnline == True:
                q.put("PRV" + " "+ self.name+ ":"+ prvmsg[1])
            else :
                self.qThread.put("NOP"+ " "+ prvmsg[0])
        elif self.isEntered == False:
            self.qThread.put("LRR")
        elif msg[0] in ["ERR", "OKG", "OKP"]:
            pass
        else:
            self.qThread.put("ERR")

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

    while True:

        queueThread = queue.Queue()
        conn, addr = server_socket.accept()
        readThread = rThread(counter, conn, addr, queueThread, userDict, isEntered, name)
        writeThread = wThread("WriteThread", conn, queueThread)

        readThread.start()
        writeThread.start()
    server_socket.close()

if __name__ == "__main__":
    main()