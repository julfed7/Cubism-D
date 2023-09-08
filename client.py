import socket
import threading
import json
import pygame
import sys
import time
import random
from pygame.math import Vector2

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("localhost", 2222))

client_id = None

response_queue = []

request_queue = []

failed_disconnect_attempts = 0

def create_response(message=None, data=None, id=client_id):
    response = {
        "response": message,
        "data": data,
        "id": id
    }
    return response.copy()

def create_request(message=None, data=None, id=client_id):
    request = {
        "request": message,
        "data": data,
        "id": id
    }
    return request.copy()

def response_sender(data):
    response = data.decode()
    response = json.loads(response)
    response_queue.append(response)
    return True

def request_sender(data):
    request_ = json.dumps(data)
    request_ = request_.encode()
    request_queue.append(request_)
    return True

def response_get_id(data):
    global client_id
    client_id = data["data"]
    print(client_id)
    return True

def response_exit(data):
    global running
    if data["data"]:
        running = False
    return True

def response_ping(data=None):
    response = create_response("pinged", None, client_id)
    request_sender(response)
    print("pinged")
    return True

def response_get_online(data):
    global hub
    try:
        hub.objects[0].set_online(data["data"])
    except:
        pass
    return True

def response_hub(data):
    game_renderer.set_scene(1)
    return True

def response_game(data):
    game_renderer.set_scene(2)
    response = create_response("joined", None, client_id)
    request_sender(response)
    return True

messages = {
    "response": {
        "get_id": response_get_id,
        "get_access_to_exit": response_exit,
        "get_online": response_get_online,
        "get_access_to_hub": response_hub
    },
    "request": {
        "ping": response_ping,
        "join_to_game": response_game
    }
}

def message_caller(data):
    messages[list(data.keys())[0]][list(data.values())[0]](data)
    return True

def data_handler():
    print("\nworker: data handler started", end="")
    while True:
        try:
            data = s.recv(1024)
            response_sender(data)
        except:
            pass
        time.sleep(0.0166666666666667)

def response_handler():
    print("\nworker: response handler started", end="")
    while True:
        if response_queue:
            for message in response_queue:
                message_caller(message)
                response_queue.remove(message)
                print("getted", message)
        time.sleep(0.0166666666666667)
                
def request_handler():
    print("\nworker: request handler started", end="")
    while True:
        if request_queue:
            for message in request_queue:
                s.send(message)
                request_queue.remove(message)
                print("sended", message)
        time.sleep(0.0166666666666667)

class Scene:
    def __init__(self):
        self.objects = []
    def tick(self):
        for object in self.objects:
            object.draw()
            object.update()

class GameRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.scenes = []
        self.current_scene = 0
    def add_scene(self, scene):
        self.scenes.append(scene)
    def delete_scene(self, scene):
        self.scenes.remove(scene)
    def next_scene(self, how=1):
        if self.current_scene+how<=len(self.scenes):
            self.current_scene+=how
    def back_scene(self, how=-1):
        if self.current_scene+how<=len(self.scenes):
            self.current_scene+=how
    def set_scene(self, how=0):
        if how<=len(self.scenes):
            self.current_scene = how
    def tick(self):
        self.scenes[self.current_scene].tick()

pygame.init()

screen = pygame.display.set_mode((1280, 720))
game_renderer = GameRenderer(screen)

class Object:
    image_button_play = pygame.image.load("button_play.png").convert_alpha()
    image_menu_start = pygame.image.load("menu_start.png").convert_alpha()
    image_menu_title = pygame.image.load("menu_title.png").convert_alpha()
    font_super_text = pygame.font.Font("Visitor Rus.ttf", 50)
    def __init__(self, image, x, y):
        self.position = Vector2(x, y)
        self.image = image
        self.rect = self.image.get_rect(center=self.position)
    def draw(self):
        game_renderer.screen.blit(self.image, self.position)
    def update(self):
        self.rect.center = self.position
    def set_scale(self, width=1, height=1):
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*width, self.image.get_height()*height))
        self.rect = self.image.get_rect(center=self.position)
    def set_position(self, x, y):
        self.position = Vector2(x, y)

class ButtonPlay(Object):
    def __init__(self, x, y):
        super().__init__(Object.image_button_play, x, y)
        self.isPressed = False
    def draw(self):
        super().draw()
    def update(self):
        super().update()
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            mouseButton = pygame.mouse.get_pressed()
            if mouseButton[0] and not self.isPressed:
                self.pressed() 
                self.isPressed = True
            elif not mouseButton[0]:
                self.isPressed = False
        else:
            self.isPressed = False
    def pressed(self):
        print("pressed")
        request = create_request("join_to_play", id=client_id)
        request_sender(request)

class MenuStart(Object):
    def __init__(self, x, y):
        super().__init__(Object.image_menu_start, x, y)
    def draw(self):
        super().draw()
    def update(self):
        super().update()

class MenuTitle(Object):
    def __init__(self, x, y):
        super().__init__(Object.image_menu_title, x, y)
    def draw(self):
        super().draw()
    def update(self):
        super().update()

class HubOnlineViewer(Object):
    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.image = Object.font_super_text
        self.online = 0
        self.text = self.image.render(f"Hub ONLINE: {self.online} / 2", False, (255, 255, 255))
        self.rect = self.text.get_rect(center=self.position)
        self.start_time = time.time()
    def draw(self):
        game_renderer.screen.blit(self.text, self.position)
    def update(self):
        super().update()
        if time.time()-self.start_time>=3:
            self.text = self.image.render(f"Hub ONLINE: {self.online} / 2", False, (255, 255, 255))
            request = create_request("online", None, client_id)
            request_sender(request)
            self.start_time = time.time()
    def set_online(self, value):
        self.online = value

class Menu(Scene):
    def __init__(self):
        super().__init__()
        menu_start = MenuStart(0, 0)
        menu_start.set_scale(80, 80)
        menu_title = MenuTitle(468, 130)
        menu_title.set_scale(8, 8)
        button_play = ButtonPlay(512, 280)
        button_play.set_scale(8, 8)
        self.objects.append(menu_start)
        self.objects.append(menu_title)
        self.objects.append(button_play)
    def tick(self):
        game_renderer.screen.fill((125, 125, 125))
        super().tick()

class Hub(Scene):
    def __init__(self):
        super().__init__()
        hub_online_viewer = HubOnlineViewer(300, 100)
        self.objects.append(hub_online_viewer)
    def tick(self):
        game_renderer.screen.fill((0, 0, 0))
        super().tick()

class Game(Scene):
    def __init__(self):
        super().__init__()
    def tick(self):
        game_renderer.screen.fill((125, 125, 125))
        super().tick()

def main():
    global screen, clock, fps, running, menu, hub, game
    clock = pygame.time.Clock()
    fps = 60
    running = True
    menu = Menu()
    hub = Hub()
    game = Game()
    game_renderer.add_scene(menu)
    game_renderer.add_scene(hub)
    game_renderer.add_scene(game)
    print("workers starting...")
    threads0 = []
    thread0 = threading.Thread(target=data_handler)
    thread1 = threading.Thread(target=response_handler)
    thread2 = threading.Thread(target=request_handler)
    threads0.append(thread0)
    threads0.append(thread1)
    threads0.append(thread2)
    for thread in threads0:
        thread.start()
    print("\nall workers started!")
    request = create_request("connect")
    request_sender(request)

if __name__ == "__main__":
    main()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            request = create_request("disconnect", id=client_id)
            request_sender(request)
            failed_disconnect_attempts += 1
            if failed_disconnect_attempts >= 10:
                running = False
    game_renderer.tick()
    pygame.display.flip()
    clock.tick(fps)
s.close()
pygame.quit()
sys.exit()
