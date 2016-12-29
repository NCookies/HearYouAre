# -*- coding: utf-8 -*-

import pygame
import os
import Queue
import memcache


class Player:
    """
    음악 재생을 하기 위해 만든 클래스
    디렉터리 내의 파일들을 큐에 넣어서 재생함
    일정 주기를 가지고 큐를 업데이트 (새로운 파일이 추가되었을 때에만)
    """
    def __init__(self):
        self.dir_path = os.getcwd() + '/res/music'
        self.music_queue = Queue.Queue()
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)

    def make_list(self):
        """
        음악 큐를 초기화함
        현재 디렉터리 안에 있는 모든 파일 포함
        :return:
        """
        pass

    def update_queue(self):
        """
        재생할 음악의 큐를 업데이트함
        일련번호를 이용하여 설정
        :return:
        """
        file_list = os.listdir(self.dir_path)
        file_list.sort()
        music_list = self.music_queue.queue

        if len(music_list) == len(file_list):
            pass

        updates = list()
        for i in range(0, len(file_list)):
            print i
            try:
                if music_list[i] in file_list:
                    pass
            except IndexError:
                updates.append(file_list[i])
                continue

        self.music_queue.put([updates[x] for x in updates])

    def play_music(self, song):
        self.play_music(song)
        pygame.init()
        pygame.mixer.music.load(song)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            self.mc.set("now_play", "")  # 현재 재생 중인 음악
            self.mc.set("play_time", "")  # 음악 재생 시간

        # 음악 플레이 큐 업데이트
        self.update_queue()


li = os.listdir(os.getcwd() + '/res/music')
li.sort()
print li
