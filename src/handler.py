# -*- coding: utf-8 -*-

from time import ctime
from src.db import DBHandler
import threading
import os
from src.db import print_error_line

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
        self.img_disc = None
        self.music_disc = None
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
                recv_data = self.client_sock.recv(BUFSIZE)
                if not recv_data:
                    break

                splitter = recv_data.split(":")
                cmd = splitter[0]
                additional_data = splitter[1:]
                print "[%s][%s] %s" % (ctime(), self.nickname, recv_data)

                # 가장 많이 요청될 것으로 생각되는 메시지 순서대로 나열함
                if cmd == "/CHECK_CONN":
                    last_id = self.dbh.get_last_id_from_music() - 1
                    if int(additional_data[0]) == last_id:
                        self.client_sock.send(make_message("CONN_OK"))
                        continue

                    self.check_conn_handler(additional_data[0])

                elif cmd == "/SEND_MUSIC":
                    # 클라이언트에서 음악 파일을 보내기 시작한다고 메시지를 받음
                    # 그에 응답하고 다음 루프 때 파일 수신 핸들러로 들어가도록 설정
                    self.client_sock.send(make_message("RECV_MUSIC"))
                    self.file_transfer_handler()

                elif cmd == "/FIRST_REQ":
                    check_send_list = self.send_music_list()

                    if check_send_list == 'none':
                        continue

                    # 전송 중 이상이 발생했으면 에러 메시지 보내고 다시 루프
                    elif not check_send_list:
                        self.client_sock.send(make_message("FAIL_RES"))
                        continue

                    # 앨범 파일 요청이 들어왔을 때 응답
                    album_req = self.client_sock.recv(BUFSIZE)
                    print album_req
                    # if album_req != "/REQ_ALBUM:":
                    #     self.client_sock.send(make_message("FAIL_RES"))
                    #     continue
                    self.send_album_images()

                elif cmd == "/REGISTER_NICKNAME":
                    # 리스트에 인자가 제대로 전달되었는지 확인
                    if len(additional_data) < 2:
                        self.client_sock.send(make_message("NICKNAME_FAIL"))
                        continue

                    # 기존에 있는 닉네임이나 등록되어 있는 MAC 이라면 예외처리를 해주어야 함
                    # 람다 함수를 통해 클라이언트에게 메시지를 보낼 수 있음
                    if not self.dbh.check_nickname(
                            self.nickname, additional_data[0], ":".join(additional_data[1:])):
                        self.client_sock.send(make_message("NICKNAME_FAIL"))
                        continue

                    # 닉네임을 MAC 주소와 함께 데이터베이스에 저장
                    # insert or replace 를 하기 때문에 기본키가 중복되더라도
                    # 새로운 닉네임을 덮어씌움
                    if self.dbh.register_device(additional_data[0], ":".join(additional_data[1:])):
                        self.nickname = additional_data[0]
                        self.dbh.set_nickname(self.nickname)
                        self.client_sock.send(make_message("NICKNAME_OK"))
                    else:
                        self.client_sock.send(make_message("NICKNAME_FAIL"))

                elif cmd == "/REQ_CLOSE":
                    self.client_sock.send(make_message("CONN_CLOSE"))
                    break

                else:
                    self.client_sock.send(make_message("RECV_MESSAGE_FAIL"))

        finally:
            print "%s is gone" % self.nickname
            self.client_sock.close()

    def check_conn_handler(self, client_latest_id):
        """
        클라이언트가 가지고 있는 음악이 최신이 아닐 때
        :return: 몰라 그런거
        """
        # 음악 예약 리스트를 보내면 클라이언트에서 필요한 앨범 이미지의 ID를 전송함
        # 일단 send부터

        self.send_music_list(require_id=client_latest_id)

        # 앨범 파일 요청이 들어왔을 때 응답
        album_req = self.client_sock.recv(BUFSIZE)
        msg, last_id = album_req.split(":")
        if not (msg == "/REQ_ALBUM"):
            self.client_sock.send(make_message("FAIL_RES"))

        # CHECK_CONN 메시지의 내용에 따라 함수의 인자를 전달함
        self.send_album_images(last_id=last_id)

    def send_music_list(self, require_id=None):
        # JSON 형태로 음악 예약 리스트를 보내야 함
        try:
            # DB 에서 JSON 형태의 데이터를 가져옴
            json_data = self.dbh.get_music_list(check_id=require_id)

            if len(json_data) <= 0:
                self.client_sock.send(make_message("{}"))
                return 'none'

            # 1024 씩 끊어서 전송
            while True:
                self.client_sock.send(json_data[:BUFSIZE-1] + '\n')
                json_data = json_data[BUFSIZE-1:]

                # 여기서 브레이크가 걸리면 메시지를 받지 않게 됨
                if len(json_data) <= 0:
                    break

                msg = self.client_sock.recv(BUFSIZE).split(":")[0]
                if msg != "/FIRST_REQ" and msg != "/CHECK_CONN":
                    print 'fuck you'
                    self.client_sock.send(make_message("FAIL_RES"))
                    break
        except ValueError as e:
            print "[%s][%s] %s" % (ctime(), self.nickname, e)
            return False

        return True

    def send_album_images(self, last_id=None):
        """
        /FIRST_REQ: last_id 는 자동으로 현재 재생 중인 음악의 ID 가 됨
        /CHECK_CONN:[ID] last_id = ID
        :param last_id: 어떤 앨범 이미지들을 보내주어야 할지 결정하는 역할
        :return:
        """
        # last_id가 None 이면 재생 중인 음악의 앨범부터
        # 명시되어 있다면 그 음악의 앨범부터
        albums = self.dbh.get_album_routes(play_now=last_id)

        # 앨범 파일들의 path 를 순회함
        for album in albums:
            # 파일 open
            with open(album[0], 'rb') as f:
                # 데이터 읽고
                data = f.read(BUFSIZE)
                # 데이터 있으면 루프 돌고
                while data:
                    self.client_sock.send(data)
                    self.client_sock.recv(BUFSIZE)
                    data = f.read(BUFSIZE)

            # 하나의 앨범 이미지의 전송을 완료했음을 알림
            self.client_sock.send(make_message("COMPLETE"))  # + albums.index(album))

    def file_transfer_handler(self):
        """
        - 파일 수신 함수
        - 먼저 SENDFILE 이라는 메시지를 받게 되면 이 핸들러를 통해 파일 송수신을 다룸
        - GET_FILE_OK 를 통해 이 핸들러로 들어올 수 있음
        :param msg: 명령어와 닉네임을 저장하고 있음
        :param data: 실제 데이터, json 또는 바이트 형태로 넘어옴
        """

        li = self.client_sock.recv(BUFSIZE).split(":")
        cmd = li[0]
        data = ":".join(li[1:])

        if cmd == "/MUSIC_INFO":
            # 음악 파일 정보(곡 이름, 가수, 재생시간 등)
            # 여기서 data[0]은 json 형태의 데이터임 => DB에 넣자
            music_file, image_file = \
                self.dbh.write_music_data(data)

            try:
                self.music_disc = open(music_file, 'wb')
                self.img_disc = open(image_file, 'wb')
            except IOError, e:
                print_error_line()
                print "[%s][%s] %s" % (ctime(), self.nickname, e)
                self.client_sock.send(make_message("RECV_MUSIC_FAIL"))
                return False

            self.client_sock.send(make_message("MUSIC_INFO_OK"))
            print "[%s][%s] Success to receive music info" % (ctime(), self.nickname)

        else:
            self.client_sock.send(make_message("RECV_MUSIC_FAIL"))
            print "[%s] Message is invalid : %s" % (self.nickname, data)

        try:
            album_data = self.client_sock.recv(BUFSIZE)
            while album_data:
                self.img_disc.write(album_data)
                self.client_sock.send(make_message("ALBUM_IMG_OK"))
                album_data = self.client_sock.recv(BUFSIZE)

                # 도대체 왜 비교 연산자로 /SEND_ALBUM_COMPLETE: 메시지를
                # 받지 못하는건지 모르겠다
                if len(album_data) != BUFSIZE:
                    self.client_sock.send(make_message("ALBUM_IMG_DONE"))
                    break

            self.img_disc.close()
        except AttributeError as e:
            print "[%s][%s] %s" % (ctime(), self.nickname, e)
            return False

        print "[%s][%s] Success to receive album image" % (ctime(), self.nickname)

        try:
            music_data = self.client_sock.recv(BUFSIZE)
            while music_data:
                self.music_disc.write(music_data)
                self.client_sock.send(make_message("MUSIC_DATA_OK"))
                music_data = self.client_sock.recv(BUFSIZE)
                if len(music_data) != BUFSIZE:
                    self.client_sock.send(make_message("MUSIC_DATA_DONE"))
                    break

            self.music_disc.close()
        except AttributeError as e:
            print "[%s][%s] %s" % (ctime(), self.nickname, e)
            return False

        print "[%s][%s] Success to receive music file" % (ctime(), self.nickname)


def make_message(msg):
    return '/' + msg + ':\n'
