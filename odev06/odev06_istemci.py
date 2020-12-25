#!/usr/bin/env python3

from client_ui import Ui_Dialog
from PyQt5 import QtWidgets, QtCore

import sys
import socket
import time
import threading
import queue

class rThread(threading.Thread):
    def __init__(self, tName, servSock, uQueue, wQueue, userQueue):
        threading.Thread.__init__(self)
        self.servSock = servSock
        self.tName = tName
        self.uQueue = uQueue
        self.wQueue = wQueue
        self.userQueue = userQueue
    
    def run(self):
        print(self.tName, "Starting.")
        while True:
            data = self.servSock.recv(1024)
            # self.uQueue.put(data.decode())
            self.incoming_parser(data.decode())
            # print(data.decode())
        print(self.tName, "Exiting.")

    def incoming_parser(self, data):
        msg = data.strip().split(" ")
        print(len(msg))
        print("Sunucu:", msg)
        if msg[0] == "\x00":
            pass
        elif msg[0] == "WEL":
            self.uQueue.put("Sunucu hosgeldiniz diyor")
        elif msg[0] == "REJ":
            self.uQueue.put("Sunucu ismini begenmedi")
        elif msg[0] == "BYE":
            self.uQueue.put("Sunucu gule gule dedi")
        
        elif msg[0] == "LST":
            #self.uQueue.put("Liste:", msg[1].replace(":",", "))
            users = msg[1].replace(":", " ").split(" ")
            for i in range(len(users)):
                self.userQueue.put(users[i])
            #self.uQueue.put("Liste:", msg[1])
        
        elif msg[0] == "NOP":
            self.uQueue.put("Kullanici %s bulunamadi" % msg[1])
        
        elif msg[0] == "ERR":
            self.uQueue.put("Hatali protokol mesaji")
        
        elif msg[0] == "LRR":
            self.uQueue.put("Once bir kendinizi tanitin")
        
        elif msg[0] == "PRV":
            prvmsg = msg[1].split(":")
            msgtoshow = " ".join(prvmsg[1:])
            self.uQueue.put("*%s*: %s" % (prvmsg[0],msgtoshow))
            self.wQueue.put("OKP\n")
        
        elif msg[0] == "GNL":
            gnlmsg = msg[1].split(":")
            msgtoshow = " ".join(gnlmsg[1:])
            self.uQueue.put("<%s>: %s" % (gnlmsg[0],msgtoshow))
            self.wQueue.put("OKG\n")

        elif msg[0] == "WRN":
            msgtoshow = " ".join(msg[1:])
            self.uQueue.put("-Sistem-: %s" % msgtoshow)
            self.wQueue.put("OKW\n")
        elif msg[0] == "TIN":
            self.wQueue.put("TON\n")
        elif msg[0] in ["ERR", "OKG", "OKP"] :
            pass
        #else:
            #self.wQueue.put("ERR\n")


class wThread(threading.Thread):
    def __init__(self, tName, servSock, wQueue):
        threading.Thread.__init__(self)
        self.servSock = servSock
        self.wQueue = wQueue
        self.tName = tName

    def run(self):
        print(self.tName, "Starting.")
        while True:
            data = self.wQueue.get()
            print("Istemci", data)
            self.servSock.send(data.encode())
        print(self.tName, "Exiting.")

class client_dialog(QtWidgets.QDialog):
    def __init__(self, wQueue, uQueue, userQueue):
        self.qt_app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QDialog.__init__(self, None)

        # create the main ui
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.wQueue = wQueue
        self.uQueue = uQueue
        self.userQueue = userQueue

        self.ui.pushButton.clicked.connect(self.buttonPressed)
        self.ui.pushButton_2.clicked.connect(self.refresh)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateText)
        self.timer.timeout.connect(self.updateListWidget)
        self.timer.start(10)
        
    def run(self):
        self.show()
        self.qt_app.exec_()
        

    def buttonPressed(self):
        if len(self.ui.lineEdit.text()) > 0:
            self.outgoing_parser(self.ui.lineEdit.text())
        self.ui.lineEdit.clear()
        self.ui.listWidget.clear()
    
    def refresh(self):
        self.outgoing_parser("/list")
        self.ui.listWidget.clear()
        
    def outgoing_parser(self, data):
        if data[0] == '/':
            splitted = data[1:].split(" ")
            if splitted[0] == "user":
                self.wQueue.put("NIC %s\n" % (splitted[1]))
                #self.wQueue.put("GLS\n")
            elif splitted[0] == "list":
                self.wQueue.put("GLS\n")
            elif splitted[0] == "quit":
                self.wQueue.put("QUI\n")
            elif splitted[0] == "msg":
                self.wQueue.put("PRV %s:%s\n" % (splitted[1], splitted[2]))
            else:
                self.ui.textBrowser.append("Komut algilanamadi")
        else:
            self.wQueue.put("GNL %s\n" % data)

    def updateText(self):
        if self.uQueue.qsize() > 0:
            data = self.uQueue.get()
            self.ui.textBrowser.append(data)

    def updateListWidget(self):
        if self.userQueue.qsize() > 0:
            data = self.userQueue.get()
            self.ui.listWidget.addItem(data)

def main():
    if not len(sys.argv) == 3:
        print("Insufficient parameters")
        return

    ip = sys.argv[1]
    port = int(sys.argv[2])

    writeQueue = queue.Queue()
    userinterfaceQueue = queue.Queue()
    userQueue = queue.Queue()
    s = socket.socket()
    # s.bind((ip,port)) # dogru kalmis aklimda, bu istemci icin gecerli degil
    s.connect((ip,port))

    app = client_dialog(writeQueue, userinterfaceQueue, userQueue)
    readThread = rThread("ReadThread", s, userinterfaceQueue, writeQueue, userQueue)
    writeThread = wThread("WriteThread", s, writeQueue)

    readThread.start()
    writeThread.start()

    app.run()

if __name__ == '__main__':
    main()
