import socket
import sys
import threading
import random
import time
class connThread(threading.Thread):
    def __init__(self, threadID, conn, c_addr):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.conn = conn
        self.c_addr = c_addr

    def run(self):
        self.conn.send("Sayi bulmaca oyununa hosgeldiniz!\n".encode())
        isStarted = False
        count = 0
        input = []
        while True:
            data = self.conn.recv(1024)
            data_str = data.decode().strip()
            print("%s : %s" %(self.c_addr, data_str))
            input = data_str.split()
            if input[0] == "STA":
                isStarted = True
                n = random.randint(1, 99)
                self.conn.send(str(n).encode())
                self.conn.send("RDY".encode())
            elif input[0] == "TIC":
                self.conn.send("TOC\n".encode())
            elif input[0] == "TRY" and (isStarted != True):
                self.conn.send("GRR\n".encode())
            elif(isStarted):
                if input[0] == "TRY":
                    self.conn.send(input[1].encode())
                    try:
                        guess = int(input[1])
                    except ValueError:
                        self.conn.send("PRR".encode())
                    if guess < n:
                        self.conn.send("LTH".encode())
                    elif guess > n:
                        self.conn.send("GTH".encode())
                    else:
                        self.conn.send("WIN".encode())  
                        time.sleep(1)
                        break
                    count += 1
                elif input[0] == "TIC":
                    self.conn.send("TOC\n".encode())
                elif input[0] == "QUI":
                    self.conn.send("BYE\n".encode())
                    break
                else :
                    self.conn.send("ERR\n".encode())
            else:
                 self.conn.send("ERR\n".encode())
            
        self.conn.close()
        print("Thread %s kapanıyor" % self.threadID)
    
server_socket = socket.socket()

live = 3
ip = "0.0.0.0"
port = int(sys.argv[1])
addr_server = (ip, port)

server_socket.bind(addr_server)
server_socket.listen(5)

counter = 0
threads = []
# live ve count değişkenlerini ekledim; ancak sürem yetmediği için bu iki değişken arasındaki ilişkiyi koduma ekleyemedim
# akşama kadar BONUS 2 'yi tamamlayacağımı düşünüyorum
while True:
    conn, addr = server_socket.accept()
    newConnThread = connThread(counter, conn, addr)
    newConnThread.start()
server_socket.close()


