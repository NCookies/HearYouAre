# -*- coding: utf-8 -*-

import socket
import sys
import handler
from time import ctime

try:
    HOST = ''
    PORT = int(sys.argv[1])
    ADDR = (HOST, PORT)
except IndexError, e:
    print "You need to specify port number"

threads = []


def close_socket(sock):
    sock.close()
    print 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno)


if __name__ == "__main__":
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_sock.bind(ADDR)
        server_sock.listen(1)
        while True:
            print "waiting for connection..."
            cli_sock, addr = server_sock.accept()
            th = handler.ThreadHandler(cli_sock, addr)
            th.start()
            threads.append(th)
            # thread.start_new_thread(thread_handler, (cli_sock, addr))

    except EOFError, e:
        print "[%s] %s" % (ctime(), e)
    except KeyboardInterrupt, e:
        print "[%s] %s" % (ctime(), e)
    except socket.error, e:
        print "[%s] %s" % (ctime(), e)
    finally:
        close_socket(server_sock)
        print "Closing..."
