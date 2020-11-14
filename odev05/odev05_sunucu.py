import socket
import sys
import threading
from datetime import datetime

class connThread(threading.Thread):
    def __init__(self, threadID, conn, c_addr):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.conn = conn
        self.c_addr = c_addr

    def run(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        self.conn.sendall(current_time.encode('utf-8'))

        while True:
            data = self.conn.recv(1024)
            data_str = data.decode().strip()
            print("%s : %s" %(self.c_addr, data_str))

            if data_str == "Selam":
                self.conn.send("Selam\n".encode())
            elif data_str == "Naber":
                self.conn.send("Iyiyim, sagol\n".encode())
            elif data_str == "Hava":
                self.conn.send("Yagmurlu\n".encode())
            elif data_str == "Haber":
                self.conn.send("Korona\n".encode())
            elif data_str == "Kapan":
                self.conn.send("Gule gule\n".encode())
                break
            else:
                 self.conn.send("Anlamadim\n".encode())
            
        self.conn.close()
        print("Thread %s kapanıyor" % self.threadID)
    
server_socket = socket.socket()

ip = "0.0.0.0"
port = int(sys.argv[1])
addr_server = (ip, port)

server_socket.bind(addr_server)
server_socket.listen(5)

counter = 0
threads = []

while True:
    conn, addr = server_socket.accept()
    newConnThread = connThread(counter, conn, addr)
    newConnThread.start()
server_socket.close()