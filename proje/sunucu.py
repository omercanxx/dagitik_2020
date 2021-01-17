import sqlite3
import socket
import sys
import threading
import queue as Q
import time
from datetime import datetime


class rThread(threading.Thread):
    def __init__(self, conn, c_addr, qThread, qLog, qDict, isEntered, name, userId, roomId):
        threading.Thread.__init__(self)
        self.conn = conn
        self.c_addr = c_addr
        self.qThread = qThread
        self.qLog = qLog
        self.qDict = qDict
        self.isEntered = isEntered
        self.name = name
        self.userId = userId
        self.roomId = roomId

    def run(self):
        dbConnection = sqlite3.connect('ChatRoom.db')
        cursor = dbConnection.cursor()
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            self.conn.sendall(current_time.encode('utf-8'))
            data = self.conn.recv(1024)
            data_str = data.decode().strip()
            print("%s : %s" % (self.c_addr, data_str))
            self.incoming_parser(data_str, current_time, cursor)
            dbConnection.commit()
        self.conn.close()
        print("Thread %s kapanıyor" % self.threadID)

    def incoming_parser(self, data, time, cur):
        # Kullanıcı ismi kontrolu için
        msg = data.strip().split(" ")

        #region Kullanıcı girişi
        if msg[0] == "NIC":
            #Kullanıcının Users tablosunda olup olmadığı kontrol ediliyor
            cur.execute('''SELECT name FROM Users;''')
            users = cur.fetchall()
            userList = []
            for user in users:
                userList.append(user[0])
            #Eğer kullanıcı tabloda var ise kullanıcının şifre kontrolü yapılıyor
            if msg[1] in userList:
                  cur.execute('''SELECT password FROM Users WHERE name = ?''', (msg[1],))
                  users = cur.fetchall()
                  user = users[0]
                  password = user[0]
                  if msg[2] == password:
                        #Kullanıcı adı ve şifre bilgisi doğru ise userId, name değişkenlerine atama yapılıyor ve queue bilgisi tutuluyor
                        self.name = msg[1]
                        cur.execute('''SELECT id FROM Users WHERE name = ?''', (self.name,))
                        users = cur.fetchall()
                        user = users[0]
                        self.userId = user[0]
                        self.isEntered = True
                        cur.execute('''UPDATE Users SET Queue = ? WHERE id = ?''', (str(self.qThread), self.userId,))
                        self.qDict[str(self.qThread)] = self.qThread
                        self.qThread.put("WEL {}\n".format(msg[1]))
                        self.qLog.put("<"+time+"> " +"WEL " + "from server to " + self.name +"\n")
                  else:
                        #Şifre yanlış ise
                        self.qThread.put("REP\n")
                        self.qLog.put("<"+time+"> " +"REP " + "from server to " + self.name +"\n")
            else:
                  #Kullanıcı adı yanlış ise
                  self.qThread.put("REJ\n")
                  self.qLog.put("<"+time+"> " +"REJ " + "from server to " + self.name +"\n")
        #endregion
        
        #region Şifre değşikliği
        elif msg[0] == "PWD" and self.isEntered:
            #Kullanıcının şifre kontrolü yapılıyor
            cur.execute('''SELECT password FROM Users WHERE id = ?''', (str(self.userId)))
            users = cur.fetchall()
            user = users[0]
            password = user[0]
            if msg[1] == password:
                if msg[2].isdecimal():
                    #Yeni şifre sadece sayılardan mı oluşuyor kontrolü yapılıyor
                    cur.execute('''UPDATE Users SET password = ? WHERE id = ?''', (msg[2], str(self.userId),))
                    self.qThread.put("WEP\n")
                    self.qLog.put("<"+time+"> " +"WEP " + "from server to " + self.name +"\n")
                else :
                    self.qThread.put("PRR\n")
                    self.qLog.put("<"+time+"> " +"PRR " + "from server to " + self.name +"\n")
            else :
                self.qThread.put("REP\n")
                self.qLog.put("<"+time+"> " +"REP " + "from server to " + self.name +"\n")
        #endregion

        #region Kullanıcı kaydı
        elif msg[0] == "REG" and self.isEntered == False:
            cur.execute('''SELECT name FROM Users;''')
            users = cur.fetchall()
            userList = []
            for user in users:
                userList.append(user[0])
            if msg[1] not in userList:
                #Kullanıcı adının kullanımda olup olmadığı kontrol ediliyor
                if msg[2].isdecimal():
                    #Şifrenin sadece sayılardan oluşup oluşmadığı kontrol ediliyor
                    cur.execute('''INSERT INTO Users (name,password, Queue)
                    VALUES (?, ?, ?)''', (msg[1], msg[2], str(self.qThread),))
                    self.name = msg[1]
                    cur.execute('''SELECT id FROM Users WHERE name = ?''', (self.name,))
                    users = cur.fetchall()
                    user = users[0]
                    #userId bilgisi güncelleniyor
                    self.userId = user[0]
                    self.isEntered = True
                    self.qThread.put("WEL\n")
                    self.qLog.put("<"+time+"> " +"WEL " + "from server to " + self.name +"\n")
                else :
                    self.qThread.put("PRR\n")
                    self.qLog.put("<"+time+"> " +"PRR " + "from server to unnamed user\n")
            else :
                self.qThread.put("RER\n")
                self.qLog.put("<"+time+"> " +"RER " + "from server to unnamed user\n")
        #endregion

        #region Kullanıcı listeleme
        elif msg[0] == "GLS" and self.isEntered:
            if self.roomId != 0:
                #Odaya giriş yapıp yapmadığımız kontrol ediliyor, eğer giriş yaptıysak User_Room tablosundan aynı odada bulunduğumuz kullanıcı bilgileri Users tablosuna join atılarak isimler listeleniyor.
                cur.execute('''SELECT name FROM Users INNER JOIN User_Room on Users.id = User_Room.userid WHERE User_Room.roomid = ?''', (self.roomId,))
                users = cur.fetchall()
                userList = []
                for user in users:
                    userList.append(user[0])
                lst = "LST"+ " "+ ":".join(userList)
                self.qThread.put(lst)
                self.qLog.put("<"+time+"> "+lst + " from server to " + self.name +"\n")
            else :
                #Henüz odaya girmediniz
                self.qThread.put("ERS")
        #endregion

        #region Oda listeleme
        elif msg[0] == "GLR" and self.isEntered:
            #Rooms tablosu listeleniyor
            cur.execute('''SELECT name
            FROM Rooms''')
            rooms = cur.fetchall()
            roomList = []
            for room in rooms:
                  roomList.append(room[0])
            lst = "LRT"+ " "+ ":".join(roomList)
            self.qThread.put(lst)
            self.qLog.put("<"+time+"> "+lst + " from server to " + self.name +"\n")
        #endregion
        
        #region Oda kurma
        elif msg[0] == "CRR" and self.isEntered:
            #Aynı isimli oda kuramaz, onun kontrolü gerçekleniyor
            cur.execute('''SELECT name
            FROM Rooms''')
            rooms = cur.fetchall()
            roomList = []
            for room in rooms:
                roomList.append(room[0])
            if msg[1] not in roomList:
                if len(msg) == 3:
                    if msg[2].isdecimal():
                        #Kapasite bilgisi sayı olarak girildi mi o kontrol ediliyor
                        cur.execute('''INSERT INTO Rooms (name, userid, capacity)
                        VALUES (?, ?, ?)''', (msg[1], self.userId, msg[2]))
                        cur.execute('''SELECT id FROM Rooms WHERE name = ?''', (msg[1],))
                        rooms = cur.fetchall()
                        room = rooms[0]
                        self.roomId = room[0]
                        cur.execute('''INSERT INTO User_Room (userid, roomid)
                        VALUES (?, ?)''', (self.userId, self.roomId))
                        print(self.roomId)
                        self.qThread.put("OKR {}\n".format(msg[1]))
                        self.qLog.put("<"+time+"> " +"OKR " + "from server to " + self.name +"\n")
        #endregion
        
        #region Odaya giriş
        elif msg[0] == "ENT" and self.isEntered:
            #Rooms tablosundan odalar listeleniyor
            cur.execute('''SELECT name
            FROM Rooms''')
            rooms = cur.fetchall()
            roomList = []
            for room in rooms:
                roomList.append(room[0])
            if msg[1] in roomList:
                cur.execute('''SELECT id, capacity FROM Rooms WHERE name = ?''', (msg[1],))
                rooms = cur.fetchall()
                room = rooms[0]
                capacity = room[1]
                if capacity != 0:
                    #Oda dolu değilse
                    cur.execute('''SELECT userid FROM BlockedUser_Room WHERE roomid = ?''', (room[0],))
                    blockedUsers = cur.fetchall()
                    blockedUserList = []
                    for blockedUser in blockedUsers:
                        blockedUserList.append(blockedUser[0])
                    if self.userId not in blockedUserList:
                        #Girmeye çalıştığımız odanın id'si üzerinden BlockedUser_Room tablosuna select atılarak engellenen kullanıcı id'leri listeye atıldı. Eğer giriş yapmaya çalışan engelli değilse devam edebiliyor
                        self.roomId = room[0]
                        #Bulunduğu odanın bilgisini tutuyoruz
                        #Odadaki kullanıcı id üzerinden giriş yapan kullanıcının ilk kaydı mı kontrol ediliyor
                        cur.execute('''SELECT userid FROM User_Room WHERE roomid = ?''', (self.roomId,))
                        users = cur.fetchall()
                        userList = []
                        for user in users:
                            userList.append(user[0])
                        #Eğer odaya ilk defa giriş yapıyorsa User_Room tablomuza kayıt atmamız lazım
                        if self.userId not in userList:
                            cur.execute('''INSERT INTO User_Room (userid, roomid)
                            VALUES (?, ?)''', (self.userId, self.roomId))
                            capacity = capacity - 1
                            cur.execute('''UPDATE Rooms 
                            SET capacity = ? WHERE id = ?''', (capacity, str(self.roomId),))
                        self.qThread.put("OKE {}\n".format(msg[1]))
                        self.qLog.put("<"+time+"> " +"OKE " + "from server to " + self.name +"\n")
                    else : 
                        self.qThread.put("EBK\n")
                        self.qLog.put("<"+time+"> EBK from server to " + self.name +"\n")
                else : 
                    self.qThread.put("KRR\n")
                    self.qLog.put("<"+time+"> KRR from server to " + self.name +"\n")
            else :
                self.qThread.put("NRR\n")
                self.qLog.put("<"+time+"> NRR from server to " + self.name +"\n")
        #endregion

        #region Genel mesaj atma
        elif msg[0] == "GNL" and self.isEntered:
            if self.roomId != 0:
                gnlmsg = " "
                gnlmsg = gnlmsg.join(msg[1:])
                #Aynı odada bulunan userid bilgileri userIds listesinde tutuluyor
                cur.execute('''SELECT userid FROM User_Room WHERE roomid = ?''', (self.roomId,))
                userIds = cur.fetchall()
                queueRoomList = []
                for userId in userIds:
                    #Tutulan id bilgisi üzerinden queue bilgileri tutuluyor
                    cur.execute('''SELECT Queue FROM Users WHERE id = ?''', (userId))
                    queues = cur.fetchall()
                    queue = queues[0]
                    queueRoomList.append(queue)
                #RoomMessage tablosuna insert atılıyor
                cur.execute('''INSERT INTO RoomMessage (roomid, userid, message) VALUES (?, ?, ?)''', (self.roomId, self.userId, gnlmsg,))
                #qDict üzerinde queue bilgilerimiz anahtar ve değer olarak string ve queue şeklinde tutuluyor. Veritabanı üzerinde queue bilgimiz string şeklinde tutulduğu için Dictionary kullandım.
                for q in queueRoomList:
                    for key in self.qDict.keys():
                        if q[0] == key:
                            value = self.qDict.get(q[0])
                            value.put("GNL" + " " + self.name + ":" + gnlmsg)
                self.qLog.put("<"+time+"> " +gnlmsg + " from " + self.name + " to everyone\n")
            else : 
                self.qThread.put("ERS\n")
        #endregion
        
        #region Özel mesaj atma
        elif msg[0] == "PRV" and self.isEntered:
            if self.roomId != 0:
                #Mesaj formatı düzenli hale getiriliyor
                prvmsg = msg[1].split(":")
                prv = prvmsg[1]
                if len(msg) > 2 :
                    p = " "
                    p = p.join(msg[2:])
                    prv = prv +" " + p
                #Aynı odada bulunan ve kullanıcının mesaj atmak istediği kuyruk bilgisi çekiliyor 
                cur.execute('''SELECT u.Queue, u.id FROM Users u INNER JOIN User_Room ur ON u.id = ur.userid WHERE u.name = ? and ur.roomid = ?''', (prvmsg[0], self.roomId,))
                queues = cur.fetchall()
                if len(queues) == 0:
                    #Sorgu null döndüyse, kimse bulunamadı demektir
                    self.qThread.put("NOP\n")
                    self.qLog.put("<"+time+"> NOP from server to " + self.name +"\n")
                else :
                    #Sorgu kuyruk bilgisini string şeklinde döndüyse Dictionary üzerinden sorgu yapılıp gerekli queue üzerine yazılır
                    q = queues[0]
                    for key in self.qDict.keys():
                        if q[0] == key:
                            value = self.qDict.get(q[0])
                            notFound = False
                            value.put("PRV" + " " + self.name + ":" + prv)
                            self.qLog.put("<" + time + ">" + prv+ " from " + self.name + " to " + prvmsg[0])
                            cur.execute('''INSERT INTO PrivateMessage (senderid, receiverid, roomid, message) VALUES (?, ?, ?, ?)''', (self.userId, q[1], self.roomId, prv,))
            else :
                self.qThread.put("ERS\n")
                self.qLog.put("<"+time+"> ERS from server to " + self.name +"\n")
                
        #endregion
        
        #region İçinde olunan oda listesi
        elif msg[0] == "GLA" and self.isEntered:
            # User_Room tablosuna userid self.userId'ye eşit olan odaların isimlerinin döndüğü sorgu yazılıyor
            cur.execute('''SELECT r.name FROM Rooms r INNER JOIN User_Room ur ON r.id = ur.roomid WHERE ur.userid = ?''', (self.userId,))
            rooms = cur.fetchall()
            if len(rooms) == 0:
                self.qThread.put("ERS\n")
                self.qLog.put("<"+time+"> ERS from server to " + self.name + "\n")
            else :
                roomList = []
                for room in rooms:
                    roomList.append(room[0])
                lat = "LAT" + " " + ":".join(roomList)
                self.qThread.put(lat)
                self.qLog.put("<"+time+"> "+lat + " from server to " + self.name +"\n")
        #endregion

        #region Odadan çıkma
        elif msg[0] == "QUI" and self.isEntered:
            if self.roomId != 0:
                #User_Room tablosundan o an içinde bulunan oda ve self.userId bilgisi kullanılarak delete işlemi gerçekleniyor
                cur.execute('''DELETE FROM User_Room WHERE userid = ? and roomid = ?''', (self.userId, self.roomId,))
                self.qThread.put("OKQ\n")
                self.qLog.put("<"+time+"> OKQ from server to " + self.name + "\n")
            else :
                self.qThread.put("ERS\n")
                self.qLog.put("<"+time+"> ERS from server to " + self.name +"\n")
        #endregion

        #region Kullanıcı odadan atma
        elif msg[0] == "KCK" and self.isEntered:
            if self.roomId != 0:
                #Yetki kontrolü gerçekleniyor, Rooms tablosu üzerindeki userid bilgisi adminin userid bilgisidir.
                cur.execute('''SELECT r.id FROM Users u INNER JOIN Rooms r ON u.id = r.userid WHERE u.id = ? and r.id = ?''', (self.userId, self.roomId,))
                roomIds = cur.fetchall()
                if len(roomIds) == 0:
                    #yetki yok
                    self.qThread("AUT\n")
                    self.qLog.put("<" + time + "> AUT from server to "+ self.name + "\n")
                else:
                    roomId = roomIds[0]
                    #Atılmak istenen kullanıcı odada mı, onun kontrolü gerçekleniyor
                    cur.execute('''SELECT u.name FROM User_Room ur INNER JOIN Users u ON ur.userid = u.id WHERE ur.roomid = ?''', (self.roomId,))
                    users = cur.fetchall()
                    userList = []
                    for user in users:
                        userList.append(user[0])
                    if msg[1] in userList:
                        #Odadaysa id bilgisi Users tablosundan name ile çekilip User_Room tablosuna delete işlemi yapılır
                        cur.execute('''SELECT id FROM Users WHERE name = ?''', (msg[1],))
                        userIds = cur.fetchall()
                        userId = userIds[0]
                        cur.execute('''DELETE FROM User_Room WHERE userid = ? and roomid = ?''', (userId[0], self.roomId,))
                        self.qThread.put("OKK\n")
                        self.qLog.put("<"+time+"> OKK from server to " + self.name + "\n")
                    else :
                        self.qThread.put("NOP\n")
                        self.qLog.put("<"+time+"> NOP from server to " + self.name + "\n")
            else:
                self.qThread("ERS\n")
                self.qLog.put("<" + time + "> ERS from server to "+ self.name + "\n")
        #endregion

        #region Oda silme
        elif msg[0] == "DEL" and self.isEntered:
            if self.roomId != 0:
                #Odanın admini kontrolü yapılıyor
                cur.execute('''SELECT r.id FROM Users u INNER JOIN Rooms r ON u.id = r.userid WHERE u.id = ? and r.id = ?''', (self.userId, self.roomId,))
                roomIds = cur.fetchall()
                if len(roomIds) == 0:
                    #yetki yok
                    self.qThread("AUT\n")
                    self.qLog.put("<" + time + "> AUT from server to "+ self.name + "\n")
                else:
                    #DEL işlemini gerçekleştiren odanın admini ise odanın isim bilgisinden id'ye ulaşılıyor
                    roomId = roomIds[0]
                    cur.execute('''SELECT name FROM Rooms WHERE userid = ?''', (self.userId,))
                    rooms = cur.fetchall()
                    roomList = []
                    for room in rooms:
                        roomList.append(room[0])
                    if msg[1] in roomList:
                        #Id üzerinden önce User_Room tablosu üzerinden daha sonra Rooms tablosu üzerinden delete işlemi gerçekleniyor
                        cur.execute('''DELETE FROM User_Room WHERE roomid = ?''', (self.roomId,))
                        cur.execute('''DELETE FROM Rooms WHERE id = ?''', (self.roomId,))
                        self.qThread.put("OKD\n")
                        self.qLog.put("<"+time+"> OKD from server to " + self.name + "\n")
                    else :
                        self.qThread.put("NOR\n")
                        self.qLog.put("<"+time+"> NOR from server to " + self.name + "\n")
            else:
                self.qThread("ERS\n")
                self.qLog.put("<" + time + "> ERS from server to "+ self.name + "\n")
        #endregion
        
        #region Kullanıcı engelleme

        elif msg[0] == "BLK" and self.isEntered:
            if self.roomId != 0:
                #Yetki kontrolü gerçekleniyor, Rooms tablosu üzerindeki userid bilgisi adminin userid bilgisidir.
                cur.execute('''SELECT r.id FROM Users u INNER JOIN Rooms r ON u.id = r.userid WHERE u.id = ? and r.id = ?''', (self.userId, self.roomId,))
                roomIds = cur.fetchall()
                if len(roomIds) == 0:
                    #yetki yok
                    self.qThread("AUT\n")
                    self.qLog.put("<" + time + "> AUT from server to "+ self.name + "\n")
                else:
                    roomId = roomIds[0]
                    #Engellenmek istenen kullanıcı odada mı, onun kontrolü gerçekleniyor
                    cur.execute('''SELECT u.name FROM User_Room ur INNER JOIN Users u ON ur.userid = u.id WHERE ur.roomid = ?''', (self.roomId,))
                    users = cur.fetchall()
                    userList = []
                    for user in users:
                        userList.append(user[0])
                    if msg[1] in userList:
                        #Odadaysa id bilgisi Users tablosundan name ile çekilip önce User_Room tablosundan delete daha sonrasında ise BlockedUser_Room tablosuna insert işlemi yapılır
                        cur.execute('''SELECT id FROM Users WHERE name = ?''', (msg[1],))
                        userIds = cur.fetchall()
                        userId = userIds[0]
                        cur.execute('''DELETE FROM User_Room WHERE userid = ? and roomid = ?''', (userId[0], self.roomId,))
                        cur.execute('''INSERT INTO BlockedUser_Room (userid, roomid) VALUES (?, ?)''', (userId[0], self.roomId,))
                        self.qThread.put("OKB\n")
                        self.qLog.put("<"+time+"> OKB from server to " + self.name + "\n")
                    else :
                        self.qThread.put("NOP\n")
                        self.qLog.put("<"+time+"> NOP from server to " + self.name + "\n")
            else:
                self.qThread("ERS\n")
                self.qLog.put("<" + time + "> ERS from server to "+ self.name + "\n")
        #endregion

        #region Kullanıcı giriş yapmadı
        elif isEntered == False:
            self.qThread("LRR\n")
            self.qLog.put("<" + time + "> LRR from server to "+ self.name + "\n")
        #endregion
        
        else:
            self.qThread.put("ERR")
            self.qLog.put("<"+time+"> ERR from server to " + self.name + "\n")

class wThread(threading.Thread):
    def __init__(self, conn, qThread):
        threading.Thread.__init__(self)
        self.conn = conn
        self.qThread = qThread

    def run(self):

        while True:
            data = self.qThread.get()
            self.conn.send(data.encode())

class lThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):

        while True:
            file = open('log.txt', 'a+')
            data = self.q.get()
            file.write(data)
            file.close()

def main():

    server_socket = socket.socket()
    queueEmpty = Q.Queue()
    
    # Kullanıcı giriş kontrolü
    isEntered = False
    name = ""
    userId = 0
    roomId = 0
    ip = "0.0.0.0"
    port = int(sys.argv[1])
    addr_server = (ip, port)
    queueDict = {}

    server_socket.bind(addr_server)
    server_socket.listen(5)

    # loglama işlemi için
    queueLog = Q.Queue()
    logThread = lThread(queueLog)
    logThread.start()
    
    while True:

        queueThread = Q.Queue()
        conn, addr = server_socket.accept()
        readThread = rThread(conn, addr, queueThread, queueLog, queueDict, isEntered, name, userId, roomId)
        writeThread = wThread(conn, queueThread)

        readThread.start()
        writeThread.start()
    server_socket.close()


if __name__ == "__main__":
    main()