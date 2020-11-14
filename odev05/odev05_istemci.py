import socket
import sys

s = socket.socket()

host = sys.argv[1]
port = int(sys.argv[2])

s.connect((host, port))
while True:
    print(s.recv(1024).decode())
    response = input("#")
    s.send(response.encode())
s.close()