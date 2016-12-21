# -*- coding: utf-8 -*-

from time import ctime
from src.db import DBHandler
import threading
import os

BUFSIZE = 1024


class ThreadHandler(threading.Thread):
    """
    - 서버에서 새로운 클라이언트를 받을 때마다 쓰레드와 그것을 다룰 핸들러 객체를 생성함
    - 파일 송수신, 연결 상태 확인, 닉네임 설정 등 여러 핸들러가 필요함
    - 핸들러들을 따로 다루기보다는 하나의 객체 내 속성으로써 사용하는 것이 편리할 것 같아
    아래와 같이 설계함
    """

    def __init__(self, *args):
        threading.Thread.__init__(self)
        self.client_sock = args[0]
        self.addr = args[1]
        self.GET_FILE_OK = False
        self.img_disc = None
        self.file_disc = None
        self.nickname = self.addr[0]
        # 데이터베이스 작업을 위한 DBHandler 객체 생성
        # SQLite3 객체는 같은 쓰레드 안에서만 작동함
        self.dbh = DBHandler(os.getcwd() + '/res/hear.db')

    def run(self):
        """
        - 상속 받은 Thread 클래스의 run 함수를 오버라이딩함
        - 받은 메시지를 split 하고 cmd 에 따라 핸들러를 호출함
        """

        print "...connected from ", self.addr[0]

        try:
            while True:
                try:
                    recv_data = self.client_sock.recv(BUFSIZE)
                    if not recv_data:
                        break

                    splitter = recv_data.split(":")
                    cmd = splitter[0]
                    additional_data = splitter[1:]
                    print "[%s][%s] %s" % (ctime(), self.nickname, recv_data)

                    # 파일 송수신을 하던 중일 때
                    if self.GET_FILE_OK is True:
                        self.file_transfer_handler([cmd, self.nickname], additional_data)

                    # 가장 많이 요청될 것으로 생각되는 메시지 순서대로 나열함
                    if cmd == "/CHECK_CONN":
                        pass

                    elif cmd == "/SEND_MUSIC":
                        # 클라이언트에서 음악 파일을 보내기 시작한다고 메시지를 받음
                        # 그에 응답하고 다음 루프 때 파일 수신 핸들러로 들어가도록 설정
                        self.client_sock.send(make_message("RECV_MUSIC"))
                        self.GET_FILE_OK = True

                    elif cmd == "/FIRST_REQ":
                        # 음악 예약 리스트를 보내야 함
                        self.client_sock.send(make_message("FIRST_RES"))

                    elif cmd == "/REGISTER_NICKNAME":
                        # 리스트에 인자가 제대로 전달되었는지 확인
                        if len(additional_data) != 2:
                            self.client_sock.send(make_message("NICKNAME_FAIL"))
                            continue

                        # 기존에 있는 닉네임이나 등록되어 있는 MAC 이라면 예외처리를 해주어야 함
                        if not self.dbh.check_nickname(self.nickname, additional_data[0]):
                            self.client_sock.send(make_message("NICKNAME_FAIL"))
                            continue

                        # 닉네임을 MAC 주소와 함께 데이터베이스에 저장
                        if self.dbh.register_device(additional_data[0], additional_data[1]):
                            self.nickname = additional_data[0]
                            self.client_sock.send(make_message("NICKNAME_OK"))
                        else:
                            self.client_sock.send(make_message("NICKNAME_FAIL"))

                    elif cmd == "/MODIFY_NICKNAME":
                        # 리스트에 인자가 제대로 전달되었는지 확인
                        if len(additional_data) != 1:
                            print "[%s][%s] Invalid Arguments" % (ctime(), self.nickname)
                            self.client_sock.send(make_message("NICKNAME_FAIL"))
                            continue

                        # 닉네임 수정
                        if self.dbh.modify_device(self.nickname, additional_data[0]):
                            self.nickname = additional_data[0]
                            self.client_sock.send(make_message("NICKNAME_OK"))
                        else:
                            self.client_sock.send(make_message("NICKNAME_FAIL"))

                    elif cmd == "/REQ_CLOSE":
                        self.client_sock.send(make_message("CONN_CLOSE"))
                        break

                    else:
                        self.client_sock.send(make_message("RECV_MESSAGE_FAIL"))

                except EOFError, e:
                    print "[%s] %s" % (ctime(), e)
                    break
                except KeyboardInterrupt, e:
                    print "[%s] %s" % (ctime(), e)
                    break

        finally:
            print "%s is gone" % self.addr[0]
            self.client_sock.close()

    def check_conn_handler(self):
        pass

    def file_transfer_handler(self, msg, data):
        """
        - 파일 수신 함수
        - 먼저 SENDFILE 이라는 메시지를 받게 되면 이 핸들러를 통해 파일 송수신을 다룸
        - GET_FILE_OK 를 통해 이 핸들러로 들어올 수 있음
        :param msg: 명령어와 닉네임을 저장하고 있음
        :param data: 실제 데이터, json 또는 바이트 형태로 넘어옴
        """
        if len(msg) != 3:
            self.client_sock.send(make_message("RECV_MUSIC_FAIL"))
            self.GET_FILE_OK = False

            return

        elif msg[0] == "/MUSIC_INFO":
            # 음악 파일 정보(곡 이름, 가수, 재생시간 등)
            # 여기서 data[0]은 json 형태의 데이터임 => DB에 넣자
            self.file_disc = open(self.dbh.write_music_data(self.nickname, data[0]), 'wb')

        elif msg[0] == "/ALBUM_IMG":
            # 앨범 이미지 파일
            # 바이너리 데이터로 수신
            self.client_sock.send(make_message("ALBUM_IMG_OK"))
            cmd = msg[0]
            write_data = data[0]

            while cmd == "/ALBUM_IMG" and write_data:
                # 파일 바이너리 데이터 수신
                self.file_disc.write(write_data)
                self.client_sock.send(make_message("ALBUM_IMG_OK"))

                try:
                    li = self.client_sock.recv(BUFSIZE).split(":")
                    del li[1]
                    cmd, write_data = li
                except ValueError:
                    self.client_sock.send(make_message("RECV_MUSIC_FAIL"))
                    self.file_disc.close()
                    self.GET_FILE_OK = False

        elif msg[0] == "/MUSIC_DATA":
            # 파일 데이터 수신, BUFSIZE 만큼씩 받아서 처리함
            self.client_sock.send(make_message("MUSIC_DATA_OK"))
            cmd = msg[0]
            write_data = data[0]

            while cmd == "/MUSIC_DATA" and write_data:
                # 파일 바이너리 데이터 수신
                self.file_disc.write(write_data)
                self.client_sock.send(make_message("MUSIC_DATA_OK"))

                try:
                    li = self.client_sock.recv(BUFSIZE).split(":")
                    del li[1]
                    cmd, write_data = li
                except ValueError:
                    self.client_sock.send(make_message("RECV_MUSIC_FAIL"))
                    self.file_disc.close()
                    self.GET_FILE_OK = False

            # 모든 파일 송수신 작업 완료 후 마무리
            print "Complete to receive music file from %s" % msg[1]
            self.file_disc.close()
            self.GET_FILE_OK = False

        print "[%s] Message is invalid : %s" % (msg[1], msg[0])
        self.client_sock.send(make_message("RECV_MUSIC_FAIL"))
        self.file_disc.close()
        self.GET_FILE_OK = False


def make_message(msg):
    return '/' + msg + ':\n'
