# -*- coding: utf-8 -*-

from socket import *
from time import ctime
import sys

HOST = "10.42.0.139"
PORT = int(sys.argv[1])
BUFSIZE = 1024
ADDR = (HOST, PORT)
# filename = sys.argv[2]

cli_sock = socket(AF_INET, SOCK_STREAM)
cli_sock.connect(ADDR)

try:
    while True:
        send_data = raw_input("> ")
        if not send_data:
            break
        cli_sock.send(send_data)

        recv_data = cli_sock.recv(BUFSIZE)

        try:
            cmd, data = str(recv_data).split(":")
        except ValueError:
            cmd = recv_data.split(":")[0]

        if not recv_data:
            break
        if cmd == "/CONNCLOSE:":
            print "Bye"
            cli_sock.close()
            exit(0)

        print "%s" % recv_data
except EOFError as e:
    print "[%s] %s" % (ctime(), e)
except KeyboardInterrupt as e:
    print "[%s] %s" % (ctime(), e)
finally:
    cli_sock.close()
