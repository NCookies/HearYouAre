# -*- coding: utf-8 -*-

"""
- main 역할을 하는 파일임
- 소켓을 열고 클라이언트에 연결돌 때마다 쓰레드를 생성함
- 각각 쓰레드는 객체를 가짐
- 기타 예외처리
- 핵심 기능들은 handler.py를 중심으로 구현함
"""

import socket
import sys
from src import handler
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
    # 소켓 객체 생성
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_sock.bind(ADDR)
        # 소켓 연결 대기
        server_sock.listen(1)
        while True:
            print "waiting for connection..."

            # 클라이언트 연결
            cli_sock, addr = server_sock.accept()

            # 쓰레드 객체에 소켓, 연결 정보, DB 핸들러 객체 전달
            th = handler.ThreadHandler(cli_sock, addr)
            th.start()
            threads.append(th)

    except EOFError, e:
        print "[%s] %s" % (ctime(), e)
    except KeyboardInterrupt, e:
        print "[%s] %s" % (ctime(), e)
    except socket.error, e:
        print "[%s] %s" % (ctime(), e)
    finally:
        close_socket(server_sock)
        print "Closing..."
