# -*- coding: utf-8 -*-

from time import ctime
import threading

BUFSIZE = 1024


class ThreadHandler(threading.Thread):
    """
    - 서버에서 새로운 클라이언트를 받을 때마다 쓰레드와 그것을 다룰 핸들러 객체를 생성함
    - 파일 송수신, 연결 상태 확인, 닉네임 설정 등 여러 핸들러가 필요함
    - 핸들러들을 따로 다루기보다는 하나의 객체 내 속성으로써 사용하는 것이 편리할 것 같아
    아래와 같이 설계함
    """

    def __init__(self, *args):
        self.client_sock = args[0]
        self.addr = args[1]
        self.file_info = None
        self.GET_FILE_OK = True
        self.file_disc = None
        threading.Thread.__init__(self)

    def run(self):
        """
        - 상속 받은 Thread 클래스의 run 함수를 오버라이딩함
        - 받은 메시지를 split 하고 cmd 에 따라 핸들러를 호출함
        """

        print "...connected from ", self.addr
        while True:
            recv_data = self.client_sock.recv(BUFSIZE)
            if not recv_data:
                break

            try:
                cmd, data = recv_data.split(":")
            except ValueError:
                cmd = recv_data.split(":")[0]

            print "[%s][%s] %s" % (ctime(), self.addr[0], recv_data)

            # 파일 송수신을 하던 중일 때
            if self.GET_FILE_OK is True:
                self.file_transfer_handler(self.client_sock.recv(BUFSIZE).split(":"))

            if cmd == "/REQCLOSE":
                print "%s is gone" % self.addr[0]
                self.client_sock.send(make_message("CONNCLOSE"))
                self.client_sock.close()

                return

            elif cmd == "/CHECKCONN":
                pass

            elif cmd == "/SENDFILE":
                self.client_sock.send(make_message("RECVFILE"))
                self.GET_FILE_OK = True

            elif cmd == "/REQNICKNAME":
                pass

            else:
                self.client_sock.send("[%s] I got message that \'%s\'" % (ctime(), recv_data))

        self.client_sock.close()

    def check_conn_handler(self):
        pass

    def file_transfer_handler(self, msg):
        """
        - 파일 수신 함수
        - 먼저 SENDFILE 이라는 메시지를 받게 되면 이 핸들러를 통해 파일 송수신을 다룸
        - GET_FILE_OK 를 통해 이 핸들러로 들어올 수 있음
        :param msg: 클라이언트로부터 받은 메시지를 split 한 리스트 형태의 데이터
        """
        if len(msg) != 2:
            self.client_sock.send(make_message("RECVFILEFAIL"))
            self.GET_FILE_OK = False
            return

        elif msg[0] == "/FILEINFO":
            # 음악 파일 정보(곡 이름, 가수, 재생시간 등)
            # 데이터는 json 형태로 넘어옴
            self.file_info = msg[1]
            # file_disc = open('./music/' + self.file_info['name'], 'wb')

        elif msg[0] == "/FILEDATA":
            # 파일 데이터 수신, BUFSIZE 만큼씩 받아서 처리함
            self.client_sock.send(make_message("FILEDATAOK"))
            cmd = msg[0]
            write_data = msg[1]

            while cmd == "/FILEDATA" and write_data:
                # 파일 바이너리 데이터 수신
                self.file_disc.write(write_data)
                self.client_sock.send(make_message("FILEDATAOK"))

                try:
                    cmd, write_data = self.client_sock.recv(BUFSIZE).split(":")
                except ValueError:
                    self.client_sock.send(make_message("RECVFILEFAIL"))
                    self.file_disc.close()
                    self.GET_FILE_OK = False

            # 모든 파일 송수신 작업 완료 후 마무리
            self.file_disc.close()
            self.file_info = None
            self.GET_FILE_OK = False

        self.GET_FILE_OK = False

    def accept_nickname_handler(self):
        pass


def make_message(msg):
    return '/' + msg + ':'
