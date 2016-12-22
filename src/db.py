# -*- coding: utf-8 -*-

import sqlite3
import json
import os
import sys
from time import ctime

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
        print db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def __del__(self):
        """
        conn 객체 제거
        """
        self.conn.close()

    def write_music_data(self, nickname, json_data):
        """
        음악 파일 정보를 DB 에 저장함
        :param nickname: 파일을 전송한 클라이언트의 닉네임
        :param json_data: 파일 정보가 들어있는 데이터,
        통째로 저장하고 json 파싱해서 저장함,
        이미 json 형태로 전달되기 때문에 따로 변환처리 할 필요가 없음
        :return 파일 디스크립터를 생성하기 위해 가각 음악 파일, 이미지 파일의 경로를 반환함
        """
        json_data = json.loads(json_data)
        # json_data = {"album": "ds", "playtime": "fd", "singer": "sdf", "name": "sd"}

        mac = self.get_mac(nickname)
        if not mac:
            print "[%s][%s] There is no device registered" % (ctime(), nickname)

        # 음악 및 앨범 파일 경로 지정
        # 맥 주소 + 받음 음악의 이름을 이용하여 설정
        music_file_route = '{0}/music/{1}_{2}'.format(DB_PATH, mac, json_data['name'])
        album_file_route = '{0}/album/{1}_{2}'.format(DB_PATH, mac, json_data['name'])

        try:
            cur = self.conn.cursor()
            insert_sql = "insert into music " \
                         "(device_mac, music_name, music_singer, music_album, " \
                         "music_playtime, music_file_route" \
                         ", music_album_image_route, music_json_data)" \
                         "values (?, ?, ?, ?, ?, ?, ?, ?)"
            cur.execute(insert_sql, (mac, json_data['name'], json_data['singer'], json_data['album'],
                                     json_data['playtime'], music_file_route,
                                     album_file_route, str(json_data)))

        except sqlite3.Error as e:
            print "[%s][%s] %s" % (ctime(), nickname, e)
            print_error_line()

            return '', ''

        self.conn.commit()

        # 저장될 음악 파일 경로 + 이름, 파일 디스크립터를 생성하기 위해 사용됨
        return music_file_route, album_file_route

    def register_device(self, nickname, mac):
        """
        맥주소와 닉네임이 새로운 것이라면 등록
        이미 맥주소가 등록되어 있다면 덮어씌움
        :param nickname: 닉네임
        :param mac: 맥주소
        """
        try:
            cur = self.conn.cursor()
            insert_sql = "insert or replace into device (device_mac, device_nickname)" \
                         "values (?, ?)"
            cur.execute(insert_sql, (mac, nickname))

        except sqlite3.Error as e:
            print "[%s][%s] %s" % (ctime(), nickname, e)
            print_error_line()
            return False

        self.conn.commit()
        return True

    def check_nickname(self, ip, nickname):
        """
        :param ip: 닉네임이 서버에 적용되기 전의 디폴트 값
        :param nickname: 변경하고자 하는 닉네임
        :return: 등록하려는 닉네임이 중복되는게 없다면 True 리턴. 있으면 False.
        """
        cur = self.conn.cursor()
        select_sql = "select * from device where device_nickname = ?"
        cur.execute(select_sql, (nickname, ))
        if cur.fetchall():
            print "[%s][%s] It already exists." % (ctime(), ip)
            return False
        return True

    def modify_device(self, old, new):
        """
        DB에서 닉네임 수정
        :param old: 기존 닉네임
        :param new: 새로운 닉네임
        """
        try:
            cur = self.conn.cursor()
            update_sql = "update device set device_nickname = ? where device_nickname = ?"
            cur.execute(update_sql, (new, old))

        except sqlite3.Error as e:
            print "[%s][%s] %s" % (ctime(), old, e)
            print_error_line()
            return False

        self.conn.commit()
        return True

    def get_mac(self, nick):
        try:
            cur = self.conn.cursor()
            select_sql = "select device_mac from device where device_nickname = ?"
            cur.execute(select_sql, (nick, ))
            return cur.fetchone()[0]

        except sqlite3.Error as e:
            print "[%s][%s] %s" % (ctime(), nick, e)
            print_error_line()
            return False

    def get_music_list(self):
        pass


def print_error_line():
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

