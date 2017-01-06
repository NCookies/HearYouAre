# -*- coding: utf-8 -*-

import pygame
import os
import Queue
import memcache
import time


NO_MORE_MUSIC = 234

pygame.mixer.music.set_endevent()


class MusicPlayer:
    """
    음악 재생을 하기 위해 만든 클래스
    디렉터리 내의 파일들을 큐에 넣어서 재생함
    일정 주기를 가지고 큐를 업데이트 (새로운 파일이 추가되었을 때에만)
    """
    def __init__(self, music_path):
        # root/res/music
        self.dir_path = os.getcwd() + music_path
        self.music_queue = Queue.Queue()

        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.mc.set("now_play", "none")
        self.mc.set("play_time", "none")

        self.make_list()

        try:
            pygame.mixer.init(44100)
        except pygame.error:
            print('Could not initialise audio.')

    def make_list(self):
        """
        음악 큐를 초기화함
        현재 디렉터리 안에 있는 모든 파일 포함
        :return:
        """
        music_list = os.listdir(self.dir_path)
        music_list.sort()
        for music in music_list:
            self.music_queue.put(music)

    # 나중에 음악의 개수가 많아지면 이 부분만 따로 멀티프로세싱으로 돌려야 할 듯
    def update_queue(self):
        """
        재생할 음악의 큐를 업데이트함
        일련번호를 이용하여 설정
        :return:
        """
        file_list = os.listdir(self.dir_path)
        file_list.sort()
        music_list = self.music_queue.queue

        # 기존의 큐와 새로 얻어온 음악 리스트가 같을 경우 패스
        if len(music_list) == len(file_list):
            return

        # 기존의 큐와 새로 만든 리스트가 중복되지 않은 값들을 얻어냄
        updates = list()
        for i in range(0, len(file_list)):
            print i
            try:
                if music_list[i] in file_list:
                    pass
            except IndexError:
                updates.append(file_list[i])
                continue

        updates.sort()
        for new in updates:
            self.music_queue.put(new)

    def play_music(self):
        if not pygame.mixer.get_init():
            return

        while True:
            try:
                # 큐에 아무것도 없다면 계속 루프를 돌면서 큐 업데이트
                # 뒤의 Empty 예외가 catch 되지 않아서 이런 방식을 사용함
                # 이에 대해서는 추후에 다시 알아봐야 할 듯
                if len(list(self.music_queue.queue)) <= 0:
                    time.sleep(3)
                    self.mc.set("now_play", "none")  # 큐에 음악이 없을 때
                    self.mc.set("play_time", "none")
                    self.update_queue()
                    continue

                song = self.dir_path + '/' + self.music_queue.get()

                # 음악 파일 사이즈가 너무 작으면 기다렸다가 다시 재생
                while os.path.getsize(song) > 500000:
                    time.sleep(3)

                print song

            # 예외 처리 루틴에 들어가지지 않음
            except Queue.Empty:
                self.mc.set("now_play", "none")  # 큐에 음악이 없을 때
                self.mc.set("play_time", "none")
                # 큐에 아무것도 없다면 잠깐 딜레이를 준 후에 다시 확인
                time.sleep(3)
                self.update_queue()
                continue

            # 현재 재생 중인 음악
            self.mc.set("now_play", os.path.split(song)[1].split("_")[0])
            try:
                pygame.mixer.music.load(song)
            except pygame.error:
                # 에러가 발생하면 5초동안 기다렸다가 큐 업데이트
                time.sleep(5)
                self.update_queue()
            pygame.mixer.music.play()
            print 'Start to play', song

            # 음악이 종료될 때까지 재생
            while pygame.mixer.music.get_busy():
                # 음악 재생 시간
                self.mc.set("play_time",
                            int(pygame.mixer.music.get_pos()) / 1000)
                # 1초마다 재생 중인 음악의 재생 시간 업데이트
                time.sleep(1)

            # 음악이 모두 플레이되었다면 삭제
            print 'End playing', song
            os.remove(song)
            # 음악 플레이 큐 업데이트
            self.update_queue()


if __name__ == "__main__":
    player = MusicPlayer('/res/music')
    player.play_music()
