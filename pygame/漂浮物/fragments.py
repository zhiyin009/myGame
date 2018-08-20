# -*-coding:utf8-*-

import pygame
import sys
import random
from pygame.locals import *
from math import *

########## 配置 #############
SCREEN_SIZE = (1920, 1080)          #分辨率
MOUSE_LINK_RADIUS = 150             #鼠标连线范围
MOUSE_SALF_RADIUS = 140             #鼠标安全范围
MOUSE_ATTRACTION = 5                #鼠标吸引力
FRAGMENT_LINK_RADIUS = 100          #碎片连线范围
FRAGMENT_SPEED = 40                 #碎片速度
FRAGMENT_MOUSE_ID = 0               #鼠标碎片ID
FRAGMENT_NUM = 100                  #碎片数量
FRAGMENT_COLOR = (135, 203, 219)    #碎片及线条颜色

class Vector():
    def __init__(self, pos):
        self.x, self.y = pos

    def __add__(self, vec):
        vec = Vector((self.x + vec.x, self.y + vec.y))
        return vec

    def __sub__(self, vec):
        vec = Vector((self.x - vec.x, self.y - vec.y))        
        return vec

    def __mul__(self, n):
        vec = Vector((self.x * n, self.y * n))
        return vec

    def get_val(self):
        return(self.x, self.y)

    def get_len(self):
        return sqrt(pow(self.x, 2) + pow(self.y, 2))

    def get_dir(self, vec):
        dist = self.get_dis(vec)
        if dist == 0: return 0
        return  Vector(((vec.x-self.x)/dist, (vec.y-self.y)/dist))

    def get_dis(self, vec):
        return sqrt(pow(vec.x-self.x, 2) + pow(vec.y-self.y, 2))

def rand_pos():
    return Vector((random.randint(0, SCREEN_SIZE[0]), random.randint(0, SCREEN_SIZE[1])))

def rand_vec():
    x = random.uniform(0, 1)
    while x == 0 or x == 1:
        x = random.uniform(0 ,1)

    return Vector((x, sqrt(1 - pow(x, 2))))

class Fragment:
    frag_num = 0
    def __init__(self, pos, vec, speed):
        self.pos = pos
        self.vec = vec
        self.speed = speed
        self.id = self.__class__.frag_num
        self.__class__.frag_num += 1

    def is_mouse(self):
        return True if self.id == FRAGMENT_MOUSE_ID else False

    def move(self, time):
        if self.is_mouse():
            self.pos = Vector(pygame.mouse.get_pos())
        else:
            self.pos = self.pos + Vector((self.vec.x*self.speed*time, self.vec.y*self.speed*time))
            # 碰壁反弹
            if self.pos.x <= 0 or self.pos.x >= SCREEN_SIZE[0]:
                self.vec.x = -self.vec.x
                self.pos.x = 0 if self.pos.x <= 0 else SCREEN_SIZE[0]
            if self.pos.y <= 0 or self.pos.y >= SCREEN_SIZE[1]:
                self.vec.y = -self.vec.y
                self.pos.y = 0 if self.pos.y <= 0 else SCREEN_SIZE[1]

    def check_and_link(self, other):
        link_dis = MOUSE_LINK_RADIUS if self.is_mouse() else FRAGMENT_LINK_RADIUS
        if self.pos.get_dis(other.pos) < link_dis:
            self.link(other)

    def link(self, other):
        LinePool.append((self, other))

        if self.is_mouse():
            # 鼠标吸引，让其逃不出范围
            link_dis = self.pos.get_dis(other.pos)
            if link_dis < MOUSE_LINK_RADIUS + 5 and link_dis > MOUSE_SALF_RADIUS:
                link_dir = self.pos.get_dir(other.pos)
                other.pos = (other.pos - link_dir * MOUSE_ATTRACTION)

def draw_all():
    # 碎片
    for frag in FragPool:
        if frag.is_mouse(): continue
        start1, stop1 = frag.pos.get_val(), (frag.pos + Vector((1, 1))).get_val()
        start2, stop2 = (frag.pos + Vector((1, 0))).get_val(), (frag.pos + Vector((0, 1))).get_val()
        pygame.draw.line(screen, FRAGMENT_COLOR, start1, stop1)
        pygame.draw.line(screen, FRAGMENT_COLOR, start2, stop2)

    # 连线
    for link in LinePool:
        start, stop = link
        dis = start.pos.get_dis(stop.pos)
        audius = MOUSE_LINK_RADIUS if start.is_mouse() else FRAGMENT_LINK_RADIUS
        color_pro = dis / audius
        color_line = []
        for i in FRAGMENT_COLOR:
            color_line.append(i*color_pro)
        pygame.draw.line(screen, color_line, start.pos.get_val(), stop.pos.get_val())


########## 各类初始化 #############
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE, FULLSCREEN, 32)
clock = pygame.time.Clock()
FragPool = []
LinePool = []

# 造碎片
for i in range(FRAGMENT_NUM):
    FragPool.append(Fragment(rand_pos(), rand_vec(), FRAGMENT_SPEED))

while True:
    # 捕捉键盘鼠标，按Esc退出
    for event in pygame.event.get():
        if event.type == QUIT:
            exit()
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            exit()

    # 移动碎片并连线
    time_passed = clock.tick(60)
    time_passed_second = time_passed / 1000.0
    LinePool = []
    for frag in FragPool:
        frag.move(time_passed_second)
        now_id = frag.id + 1
        while now_id < len(FragPool):
            frag.check_and_link(FragPool[now_id])
            now_id += 1

    screen.fill((255, 255, 255))
    draw_all()
    pygame.display.update()
