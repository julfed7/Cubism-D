import os
import sys
import json
import pygame
import time

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
    def __init__(self, path):
        self.path = path
        self.surface = None
    def setup(self):
        self.set_surface(pygame.image.load(path(self.get_path())))
    def get_path(self):
        return self.path
    def set_surface(self, new_surface):
        self.surface = new_surface
    def get_surface(self):
        return self.surface

class Window:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.title = "game window"
        self.surface = None
        self.icon_image = None
        self.virtual_surface = None
    def setup(self):
        pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.set_surface(pygame.display.get_surface())
        self.set_virtual_surface(pygame.Surface((self.get_width(), self.get_height())))
    def update(self):
        pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption(self.get_title())
        pygame.display.set_icon(self.get_icon_image().get_surface())
    def draw(self, image, position):
        self.get_virtual_surface().blit(image.get_surface(), (position[0], position[1]))
    def tick(self):
        window_size = self.get_surface().get_size()
        size = (window_size[1]/9*16, window_size[1])
        position = (window_size[0]/2-size[0]/2, window_size[1]/2-size[1]/2)
        scaled_virtual_surface = pygame.transform.scale(self.get_virtual_surface(), size)
        self.get_surface().blit(scaled_virtual_surface, position)
        pygame.display.flip()
    def fill(self, color):
        self.get_virtual_surface().fill(color)
    def set_surface(self, new_surface):
        self.surface = new_surface
    def get_surface(self):
        return self.surface
    def get_width(self):
        return self.width
    def get_height(self):
        return self.height
    def set_title(self, new_title):
        self.title = new_title
    def get_title(self):
        return self.title
    def set_icon_image(self, new_image):
        self.icon_image = new_image
    def get_icon_image(self):
        return self.icon_image
    def set_virtual_surface(self, new_surface):
        self.virtual_surface = new_surface
    def get_virtual_surface(self):
        return self.virtual_surface

class Event:
    def __init__(self, type, key):
        self.type = type
        self.key = key
    def set_type(self, new_type):
        self.type = new_type
    def get_type(self):
        return self.type
    def set_key(self, new_key):
        self.key = new_key
    def get_key(self):
        return self.key

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

pygame.init()

window = Window(WIDTH, HEIGHT)
window.setup()

screen = window.get_surface()

window.set_title(TITLE)

icon_image = Image(path("sprites/icon.png"))
icon_image.setup()

window.set_icon_image(icon_image)

window.update()

print(pygame.display.Info())

while is_running:
    for event in get_events():
        if event.get_type() == pygame.QUIT:
            is_running = False
        elif event.get_type() == pygame.KEYUP:
            if event.get_key() == pygame.K_ESCAPE:
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