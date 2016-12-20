# -*- coding: utf-8 -*-

from socket import *
from time import ctime
import sys

HOST = "127.0.0.1"
PORT = int(sys.argv[1])
BUFSIZE = 1024
ADDR = (HOST, PORT)
filename = sys.argv[2]

cli_sock = socket(AF_INET, SOCK_STREAM)
cli_sock.connect(ADDR)

f = open(filename, 'rb')
try:
    cli_sock.send("/SENDFILE:")
    cli_sock.recv(BUFSIZE)
    file_data = f.read(BUFSIZE)
    while file_data:
        cli_sock.send(file_data)
        file_data = f.read(BUFSIZE)

        recv_data = cli_sock.recv(BUFSIZE)

        try:
            cmd, data = str(recv_data).split(":")
        except ValueError:
            cmd = recv_data.split(":")[0]

        print "%s" % recv_data
except EOFError as e:
    print "[%s] %s" % (ctime(), e)
except KeyboardInterrupt as e:
    print "[%s] %s" % (ctime(), e)
finally:
    f.close()
    cli_sock.close()
