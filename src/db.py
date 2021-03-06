# -*- coding: utf-8 -*-

import sqlite3
import json
import os
import sys
from time import ctime
import memcache

DB_PATH = os.getcwd() + '/res'


"""
music_id integer primary key autoincrement,
device_mac text,
music_name text not null,
music_singer text,
music_album text,
music_playtime text,
music_file_route text,
music_album_image_route text
music_json_data json,
"""


class DBHandler:
    def __init__(self, db_path):
        """
        conn 객체 생성
        :param db_path: 데이터베이스 파일 경로
        """
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.nickname = ''

    def __del__(self):
        """
        conn 객체 제거
        """
        self.conn.close()

    def set_nickname(self, nick):
        self.nickname = nick

    def write_music_data(self, json_data):
        """
        음악 파일 정보를 DB 에 저장함
        :param json_data: 파일 정보가 들어있는 데이터,
        통째로 저장하고 json 파싱해서 저장함,
        이미 json 형태로 전달되기 때문에 따로 변환처리 할 필요가 없음
        :return 파일 디스크립터를 생성하기 위해 가각 음악 파일, 이미지 파일의 경로를 반환함
        """

        try:
            data = json.loads(json_data)
        except ValueError:
            print "[%s][%s] JSON format is invalid" % (ctime(), self.nickname)
            return '', ''

        # data = {"album": "안녕", "playtime": "fd", "singer": "sdf", "name": "sd"}

        mac = self.get_mac()
        if not mac:
            print "[%s][%s] There is no device registered" % (ctime(), self.nickname)
            return '', ''

        # 가장 나중에 등록한 music ID를 얻어와 음악 및 앨범 파일 앞에 붙임
        # 음악을 재생할 때 순서를 편리하게 설정하기 위해서 하였음
        # 만약 함수의 리턴값이 아무것도 없다면 기존에 등록된 음악이 없다고 가정하고 1부터 시작함
        music_id = self.get_last_id_from_music()

        # 음악 및 앨범 파일 경로 지정
        # 맥 주소 + 받음 음악의 이름을 이용하여 설정
        music_file_route = '{0}/music/{1}_{2}'.format(DB_PATH, music_id, mac)
        album_file_route = '{0}/album/{1}_{2}'.format(DB_PATH, music_id, mac)
        print json_data

        try:
            cur = self.conn.cursor()
            insert_sql = "insert into music " \
                         "(device_mac, music_name, music_singer, music_album, " \
                         "music_playtime, music_file_route" \
                         ", music_album_image_route, music_json_data)" \
                         "values (?, ?, ?, ?, ?, ?, ?, ?)"
            cur.execute(insert_sql, (mac, data['name'], data['singer'], data['album'],
                                     data['playtime'], music_file_route,
                                     album_file_route, str(data).replace("'", '"')))

        except sqlite3.Error as e:
            print "[%s][%s] %s" % (ctime(), self.nickname, e)
            print_error_line()

            return '', ''

        self.conn.commit()

        # 저장될 음악 파일 경로 + 이름, 파일 디스크립터를 생성하기 위해 사용됨
        return music_file_route, album_file_route

    def register_device(self, nick, mac):
        """
        맥주소와 닉네임이 새로운 것이라면 등록
        이미 맥주소가 등록되어 있다면 덮어씌움
        :param nick: 닉네임
        :param mac: 맥주소
        """
        try:
            cur = self.conn.cursor()
            insert_sql = "insert or replace into device (device_mac, device_nickname)" \
                         "values (?, ?)"
            cur.execute(insert_sql, (mac, nick))

        except sqlite3.Error as e:
            print "[%s][%s] %s" % (ctime(), nick, e)
            print_error_line()
            return False

        self.conn.commit()
        return True

    def check_nickname(self, ip, nick, mac):
        """
        :param ip: 닉네임이 서버에 적용되기 전의 디폴트 값
        :param nick: 변경하고자 하는 닉네임
        :param mac: 중복된 닉네임이 이전에 등록되었던 디바이스인지 확인하기 위해서 사용
        :param send_msg: 메시지를 보내는 람다 함수를 인자로 받음
        :return: 등록하려는 닉네임이 중복되는게 없다면 True 리턴. 있으면 False.
        """
        cur = self.conn.cursor()
        select_sql = "select * from device where device_nickname = ?"
        cur.execute(select_sql, (nick, ))
        fetch = cur.fetchone()

        # 중복되는 닉네임이 있는지 검사
        if fetch:
            # 이전에 접속했던 디바이스가 다시 등록하는 것이라면
            if fetch[0] == mac:
                    return True
                # send_msg("NICKNAME_OK")

            # 닉네임을 요청한 디바이스의 맥주소와
            # 겹치는 닉네임을 가지고 있는 디바이스의 맥주소가 다르다면
            else:
                print "[%s][%s] It already exists." % (ctime(), ip)
                # send_msg("NICKNAME_FAIL")

            return False

        # 중복되는 닉네임이 없으면 OK
        return True

    def get_mac(self):
        """
        맥 주소를 얻기 위한 함수
        :param nick: 닉네임을 이용하여 맥 주소를 얻음
        :return:
        """
        try:
            cur = self.conn.cursor()
            select_sql = "select device_mac from device where device_nickname = ?"
            # 닉네임이 등록되어 있지 않으면 오류 발생
            cur.execute(select_sql, (self.nickname, ))
            try:
                return cur.fetchone()[0]
            except TypeError as e:
                print "[%s][%s] %s" % (ctime(), self.nickname, e)
                return False

        except sqlite3.Error as e:
            print "[%s][%s] %s" % (ctime(), self.nickname, e)
            print_error_line()
            return False

    def get_music_list(self, check_id=None):
        """
        음악 리스트를 json 형태로 가져옴
        여기서 오류가 나지 않기 위해서는 DB에 정상적인 형태의 json이 들어가 있어야 함
        :return: 예약 리스트와 재생 중인 음악의 정보를 담고 있는 JSON Object 리턴
        """

        if check_id is None:
            check_id = self.get_now_play()

        try:
            cur = self.conn.cursor()
            select_sql = "select music_id, music_name, music_singer, " \
                         "music_album, music_playtime from music where music_id >= ?"

            # 재생 중인 음악이 없다면 공백 리턴
            if self.get_now_play() == "none":
                return ''
            cur.execute(select_sql, (check_id, ))

        except sqlite3.Error as e:
            print "[%s] %s" % (ctime(), e)
            print_error_line()
            return False

        # JSON 객체를 만들기 위한 dictionary
        data = {
            'music_list': [

            ],
            'playing_music': [
                {
                    'music_id': '',
                    'play_time': ''
                }
            ]
        }

        try:
            music_id = int(check_id)

        # 재생 중이거나 예약된 음악이 아무것도 없을 때
        except ValueError:
            return ''

        # 예시 데이터. select 한 순으로 나옴
        # (11, u'11:11.mp3', u'\ud0dc\uc5f0 (TAEYEON)', u'11:11', u'223478')

        for row in cur.fetchall():
            music_arr = dict()
            music_arr['id'] = row[0]
            music_arr['name'] = row[1]
            music_arr['singer'] = row[2]
            music_arr['album'] = row[3]
            music_arr['playtime'] = row[4]
            music_arr['nickname'] = self.nickname
            data['music_list'].append(music_arr)

        data['playing_music'][0]['music_id'] = music_id
        data['playing_music'][0]['play_time'] = self.mc.get("play_time")

        print json.dumps(data, indent=4)
        return json.dumps(data)

    def get_now_play(self):
        """
        현재 재생 중인 음악의 ID를 memcache 를 통해 얻어옴
        :return: 현재 재생 중인 음악 ID
        """
        return self.mc.get("now_play")

    def get_album_routes(self, play_now=None):
        """
        현재 예약 리스트에 있는 음악 앨범 파일의 경로를 얻어오는 함수
        절대경로임
        :return: 앨범 파일들의 path 리턴
        """
        # 요청이 /FIRST_REQ 로 들어온 경우
        if play_now is None:
            play_now = self.get_now_play()

        try:
            cur = self.conn.cursor()
            select_sql = "select music_album_image_route from music where music_id >= ?"
            cur.execute(select_sql, (play_now, ))
        except sqlite3.Error as e:
            print "[%s] %s" % (ctime(), e)
            print_error_line()
            return False

        return cur.fetchall()

    def get_last_id_from_music(self):
        """
        음악 ID의 가장 마지막 인덱스를 가져옴
        :return:
        """
        try:
            cur = self.conn.cursor()
            select_sql = "select music_id from music where music_id = (select max(music_id) from music)"
            cur.execute(select_sql)

        except sqlite3.Error as e:
            print "[%s][%s] %s" % (ctime(), self.nickname, e)
            print_error_line()
            return False

        except TypeError:
            return None

        # cur.fetchone() 을 하면 다음에 다시 할 때 인덱스가 이동함
        # 그래서 변수에 저장하여 사용해야 함
        music_id = 1
        try:
            # 가장 마지막 아이디에서 +1
            music_id = int(cur.fetchone()[0]) + 1
        # 만약 music 테이블에 아무 데이터도 없다면 그대로 1 return
        except TypeError:
            return music_id

        # 정상적으로 값을 얻어왔다면 music_id return
        return music_id


def print_error_line():
    """
    에러가 발생한 라인 출력
    :return:
    """
    print 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno)

a = {
    'music1': [
        {'name': 'aa',
         'album': 'bb'}
        ],
    'music2': [
        {'name': 'cc',
         'album': 'dd'''}
        ]
}

j = json.dumps(a, indent=4)

"""
{
    "music1": [
        {
            "album": "bb",
            "name": "aa"
        }
    ],
    "music2": [
        {
            "album": "dd",
            "name": "cc"
        }
    ]
}
"""

# print j

