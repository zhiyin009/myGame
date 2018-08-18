#-*- coding:utf8 -*-

import pygame
import time
import random
from pygame.locals import *
from sys import exit
from math import *

########## 配置 #############
SCREEN_SIZE = (1920, 1080)      #分辨率
FISH_ATK_DIS = 40               #鱼的攻击范围
WORM_IMG_FILE = "worm.png"      #蚯蚓图
SEA_IMG_FILE = "sea.jpg"        #背景图
FISH_IMG_FILE = ["fish_move_0.png", "fish_move_1.png", "fish_move_2.png"]   #鱼图片
FISH_BIRTH_POINT = ((0, 0), (SCREEN_SIZE[0], 0), (0, SCREEN_SIZE[1]), (SCREEN_SIZE))    # 出生点
FISH_NUM_MAX = 100              #鱼条数
FISH_BORN_TIME = 0.3            #鱼产生间隔
FISH_SPEED = 180                #鱼速度
FISH_HIT_RADIUS = 45            #鱼碰撞半径
FRAMES_DELAY_MAX = 16           #鱼动画延迟帧数

class Vector():
    def __init__(self, pos):
        self.x, self.y = pos

    def add(self, vec):
        self.x += vec.x
        self.y += vec.y

    def dec(self, vec):
        self.x -= vec.x
        self.y -= vec.y

    def mul(self, n):
        self.x *= n
        self.y *= n

    def get_len(self):
        return sqrt(pow(self.x, 2) + pow(self.y, 2))

    def get_dir(self, vec):
        dist = self.get_dis(vec)
        if dist == 0: return 0
        return  Vector(((vec.x-self.x)/dist, (vec.y-self.y)/dist))

    def get_dis(self, vec):
        return sqrt(pow(vec.x-self.x, 2) + pow(vec.y-self.y, 2))

class Fish():
    fish_num = 0
    def __init__(self, vec, radius=FISH_HIT_RADIUS):
        self.pos = Vector(vec)
        self.speed = 0
        self.angle = 0              #用来画图旋转角度
        self.hit_radius = radius    #碰撞半径
        self.frames_delay = 0         #用于帧播放
        self.fish_now_frames = 1
        self.tail_dir = 1

    def get_pos(self):
        return Vector(self.pos)

    def move(self, worm_vec, time):
        pos = self.pos

        # 撞到兄弟了，弹开
        for fish in fish_pool:
            if self is not fish and self.is_hit(fish):
                dis = pos.get_dis(fish.pos)
                self.speed = (FISH_SPEED * dis / 10)
                m_dir = pos.get_dir(fish.pos)
                fish.pos.add(Vector((m_dir.x*self.speed*time, m_dir.y*self.speed*time)))
                pos.dec(Vector((m_dir.x*self.speed*time, m_dir.y*self.speed*time)))
                return

        dis = pos.get_dis(worm_vec)
        self.speed = (FISH_SPEED * dis / 100)
        m_dir = pos.get_dir(worm_vec)
        pos.add(Vector((m_dir.x*self.speed*time, m_dir.y*self.speed*time)))
        self.rotate(worm_vec)

    def rotate(self, vec):
        fish_dir = self.pos.get_dir(vec)
        fish_cos = acos(fish_dir.x/fish_dir.get_len())
        if fish_dir.y > 0: fish_cos = -fish_cos
        self.angle = fish_cos/pi*180 - 90

    def blit(self, surface=None):
        scn = screen
        frames_delay, fish_now_frames, tail_dir = self.frames_delay, self.fish_now_frames, self.tail_dir
        if surface is not None: #图片打印区域
            scn = surface

        if fish_now_frames+tail_dir < 0 or fish_now_frames+tail_dir >= len(FISH_IMG_FILE):   #设置尾巴方向
            self.tail_dir = -tail_dir

        if frames_delay >= FRAMES_DELAY_MAX:    #设置鱼图片
            self.frames_delay %= FRAMES_DELAY_MAX
            self.fish_now_frames += tail_dir
        self.frames_delay += 1

        fish_rotated = pygame.transform.rotate(fish_img[fish_now_frames], self.angle)   #旋转
        f_draw_pos = (self.pos.x-fish_img_size[0]/2, self.pos.y-fish_img_size[1]/2)
        scn.blit(fish_rotated, f_draw_pos)

    def get_dis(self, fish):
        return self.pos.get_dis(fish.pos)

    def is_hit(self, fish):
        if self.get_dis(fish) < self.hit_radius:
            return True
        return False

    @classmethod
    def fish_born(cls):
        fish_pool.append(Fish(FISH_BIRTH_POINT[random.randint(0,3)]))
        Fish.fish_num += 1


########## 各类初始化 #############
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE, FULLSCREEN, 32)   # 屏幕尺寸 全屏
mfont = pygame.font.Font(None, 32)                              # ttf文件位置及字体大小
pygame.mouse.set_visible(False)                                 # 关闭光标显示

# 载入鱼、蚯蚓、背景图片
fish_img = []
for i in range(3):
    fish_img.append(pygame.image.load(FISH_IMG_FILE[i]).convert_alpha())
worm_img = pygame.image.load(WORM_IMG_FILE).convert_alpha()
sea_img = pygame.transform.scale(pygame.image.load(SEA_IMG_FILE).convert_alpha(), SCREEN_SIZE)
fish_img_size = fish_img[0].get_size()
worm_img_size = worm_img.get_size()
fish_born_stamp = 0

# 时钟
clock = pygame.time.Clock()
alive_time_stamp = time.time()


# 简陋鱼池（放鱼的）
fish_pool = []

# 打印所有图片
def draw_all():
    font_size = mfont.size('')
    w_pos = (mouse_v.x-worm_img_size[0]/2, mouse_v.y-worm_img_size[1]/2)

    screen.blit(sea_img, (0, 0))
    screen.blit(worm_img, w_pos)    
    for i in fish_pool:
        i.blit()
    text = mfont.render(u"%.2f" % float(time.time()-alive_time_stamp), True, (0, 125, 0))
    screen.blit(text, ((SCREEN_SIZE[0])/2, SCREEN_SIZE[1]/2))

while True:
    # 捕捉键盘鼠标，按Esc退出
    for event in pygame.event.get():
        if event.type == QUIT:
            exit()
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            exit()

    # 造鱼
    if Fish.fish_num < FISH_NUM_MAX and fish_born_stamp < time.time()-FISH_BORN_TIME:
        fish_born_stamp = time.time()
        Fish.fish_born()

    # 按照60fps的速度刷新鱼，否则会因电脑差异影响游速
    time_passed = clock.tick(60)
    time_passed_second = time_passed / 1000.0
    mouse_v = Vector(pygame.mouse.get_pos())
    is_over = False
    for fish in fish_pool:
        fish.move(mouse_v, time_passed_second)
        if fish.pos.get_dis(mouse_v) <= FISH_ATK_DIS:
            is_over = True
            alive_time_stamp = time.time() - alive_time_stamp
    if is_over: break;

    draw_all()
    pygame.display.update()

while True:
    # 捕捉键盘，按Esc退出
    for event in pygame.event.get():
        if event.type == QUIT:
            exit()
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            exit()
                
    # 打印成绩
    screen.fill((0, 0, 0))
    text = mfont.render(u"%.2f" % alive_time_stamp, True, (0, 125, 0))
    screen.blit(text, ((SCREEN_SIZE[0])/2, SCREEN_SIZE[1]/2))
    pygame.display.update()                                      
