import os
import sys
import json
import pygame
import time
import logic

def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)
    
def path(this_path, environtment_os="android"):
    if environtment_os == "windows":
        return resource_path(this_path)
    else:
        return this_path

def read_file_json(path):
    with open(path) as file:
        data = file.read()
        book = json.loads(data)
    return book
    
def read_file(path):
    if "/" in path:
        file_name = path.split("/")[-1]
    else:
        file_name = path.split("\\")[-1]
    file_type = file_name.split(".")[-1]
    if file_type == "json":
        return read_file_json(path)

def get_events():
    return [Event(event.type, event.key if hasattr(event, "key") else None) for event in pygame.event.get()]

class Image:
    def __init__(self):
        self.surface = None

class Window:
    def __init__(self, width, height):
        self.__width = width
        self.__height = height
        self.__virtual_surface = None
        self.icon_image = None
        self.surface = None
        self.title = "pygame window"
    def setup(self):
        pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.surface = pygame.display.get_surface()
        self.virtual_surface = pygame.Surface((self.width, self.height))
    def update(self):
        pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption(self.title)
        pygame.display.set_icon(self.icon_image.surface)
    def draw(self, image, position):
        self.virtual_surface.blit(image.surface, (position[0], position[1]))
    def tick(self):
        window_size = self.surface.get_size()
        size = (window_size[1]/9*16, window_size[1])
        position = (window_size[0]/2-size[0]/2, window_size[1]/2-size[1]/2)
        scaled_virtual_surface = pygame.transform.scale(self.virtual_surface, size)
        self.surface.blit(scaled_virtual_surface, position)
        pygame.display.flip()
    def fill(self, color):
        self.virtual_surface.fill(color)
    @property
    def width(self):
        return self.__width
    @property
    def height(self):
        return self.__height
    @property
    def virtual_surface(self):
        return self.__virtual_surface
    @virtual_surface.setter
    def virtual_surface(self, new_surface):
        self.__virtual_surface = new_surface

class Event:
    def __init__(self, type, key):
        self.type = type
        self.key = key

ticks = 0

last_time = time.time()
delta_time = last_time/1000

is_running = True

environtment_os = "android"		
        
config = read_file(path("settings/app.json"))

TITLE = config["Title"]

FPS = config["FPS"]

WIDTH = config["Width"]

HEIGHT = config["Height"]

icon_file_name = config["Icon_file_name"]

game = logic.Game()

scene = logic.Scene()

game_object = logic.GameObject()

scene.add_game_object(game_object)

pygame.init()

window = Window(WIDTH, HEIGHT)
window.setup()

screen = window.surface

window.title = TITLE

icon_image = Image()
icon_image.surface = pygame.image.load("sprites/icon.png")

window.icon_image = icon_image

window.update()

print(pygame.display.Info())

while is_running:
    for event in get_events():
        if event.type == pygame.QUIT:
            is_running = False
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE:
                is_running = False
    window.fill((255, 255, 255))
    window.tick()
    ticks += 1
    delta_time = time.time()-last_time
    last_time = time.time()
    sleep_time = 1/60 - delta_time
    if sleep_time < 0:
        sleep_time = 0
    time.sleep(sleep_time)
pygame.quit()