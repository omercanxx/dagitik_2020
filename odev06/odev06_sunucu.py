import socket
import sys
import threading
import queue
from datetime import datetime

class rThread(threading.Thread):
    def __init__(self, threadID, conn, c_addr, wQueue, uDict):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.conn = conn
        self.c_addr = c_addr
        self.wQueue = wQueue
        self.uDict = uDict

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
        isEntered = False
        msg = data.strip().split(" ")

        if msg[0] == "NIC":
            if msg[1] not in self.uDict.keys():
                self.uDict[msg[1]] = self.conn
                isEntered = True
                self.wQueue.put("WEL")
            else:
                self.wQueue.put("REJ")
        else:
            self.wQueue.put("LRR")

class wThread(threading.Thread):
    def __init__(self, tName, conn, queue):
        threading.Thread.__init__(self)
        self.conn = conn
        self.queue = queue
        self.tName = tName

    def run(self):
        print(self.tName, "Starting.")
        while True:
            data = self.queue.get()
            self.conn.send(data.encode())
        print(self.tName, "Exiting.")


def main():
    server_socket = socket.socket()
    userDict = {}
    ip = "0.0.0.0"
    port = int(sys.argv[1])
    addr_server = (ip, port)

    server_socket.bind(addr_server)
    server_socket.listen(5)

    counter = 0
    threads = []

    while True:
        q = queue.Queue()

        conn, addr = server_socket.accept()
        readThread = rThread(counter, conn, addr, q, userDict)
        writeThread = wThread("WriteThread", conn, q)

        readThread.start()
        writeThread.start()
    server_socket.close()

if __name__ == "__main__":
    main()