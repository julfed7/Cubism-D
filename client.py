import socket
import threading
import json
import pygame
import sys
import time
import random
from pygame.math import Vector2

current_scene = 0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.connect(("localhost", 2222))
except:
    current_scene = 3
finally:
    print("Client running. Version 1.0")

client_id = None

response_queue = []

request_queue = []

failed_disconnect_attempts = 0

camera_offset_x = 0
camera_offset_y = 0
camera_offset_z = 0
camera_locked = True

delta = 0

t1 = time.time()

def delta_update():
    global delta, t1
    t2 = time.time()
    delta = t2-t1
    t1 = t2

def remove_object(id):
    for object in game_renderer.scenes[game_renderer.current_scene].objects:
        if object.id == id:
            game_renderer.scenes[game_renderer.current_scene].objects.remove(object)

def add_object(object):
    game_renderer.scenes[game_renderer.current_scene].objects.append(object)   

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
    print("switched to hub scene")
    game_renderer.set_scene(1)
    return True

def response_game(data):
    print("switched to game scene")
    game_renderer.set_scene(2)
    response = create_response("joined", None, client_id)
    request_sender(response)
    return True

def response_get_objects(data):
    global game
    for object in game.objects:
        isIn = False
        for game_object in data["data"]:
            if game_object["id"] == object.id:
                isIn = True
        if not isIn:
            remove_object(object.id)
    for game_object in data["data"]:
        isIn = False
        for object in game.objects:
            if object.id == game_object["id"]:
                isIn = True
        if not isIn:
            player = Player(game_object["id"], game_object["x"], game_object["y"])
            player.set_scale(5, 5)
            add_object(player)
    return True

def response_get_error_disconnect_game_started(data):
    print("switched to error disconnect game started scene")
    game_renderer.set_scene(4)
    return True

def response_get_access_to_leave_hub(data):
    print("switched to menu scene")
    game_renderer.set_scene(0)

messages = {
    "response": {
        "get_id": response_get_id,
        "get_access_to_exit": response_exit,
        "get_online": response_get_online,
        "get_access_to_hub": response_hub,
        "get_objects": response_get_objects,
        "get_error_disconnect_game_started": response_get_error_disconnect_game_started,
        "get_access_to_leave_hub": response_get_access_to_leave_hub
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
    error_count = 0
    print("\nworker: request handler started", end="")
    while True:
        if request_queue:
            for message in request_queue:
                try:
                    s.send(message)
                    request_queue.remove(message)
                    print("sended", message)
                except OSError:
                    error_count += 1
                    if error_count <= 1:
                        print("error. Request can't be sended")
        time.sleep(0.0166666666666667)

class Scene:
    def __init__(self):
        self.objects = []
        self.ticks = 0
    def setup(self):
        pass
    def tick(self):
        self.ticks += 1
        if self.ticks == 1:
            self.setup()
        for object in self.objects:
            image = pygame.transform.scale(object.image, (object.rect.width+camera_offset_z, object.rect.height+camera_offset_z))
            game_renderer.screen.blit(image, (object.rect.x+camera_offset_x, object.rect.y+camera_offset_y))
            object.tick()

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

screen = pygame.display.set_mode((1280, 720), pygame.FULLSCREEN)
game_renderer = GameRenderer(screen)

class Object:
    image_menu_gui_button_play = pygame.image.load("button_play.png").convert_alpha()
    image_menu_gui_bg_start = pygame.image.load("menu_start.png").convert_alpha()
    image_menu_spr_title = pygame.image.load("menu_title.png").convert_alpha()
    image_game_spr_churka = pygame.image.load("churka.png").convert_alpha()
    font_super_text = pygame.font.Font("hub.ttf", 50)
    font_small_text = pygame.font.Font("hub.ttf", 25)
    def __init__(self, id, image, x, y):
        self.id = id
        self.image = image
        self.position = Vector2(x, y)
        self.rect = self.image.get_rect(center=self.position)
        self.ticks = 0
    def setup(self):
        pass
    def tick(self):
        self.ticks += 1
        if self.ticks == 1:
            self.setup()
        self.image.get_rect(center=self.position)
    def set_scale(self, width=1, height=1):
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*width, self.image.get_height()*height))
        self.rect = self.image.get_rect(center=self.position)
    def set_position(self, x, y):
        self.position = Vector2(x, y)

class ButtonPlay(Object):
    def __init__(self, x, y):
        super().__init__(random.randint(10001, 20001), Object.image_menu_gui_button_play, x, y)
        self.isPressed = False
    def tick(self):
        super().tick()
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
        super().__init__(random.randint(10001, 20001), Object.image_menu_gui_bg_start, x, y)
    def tick(self):
        super().tick()

class MenuTitle(Object):
    def __init__(self, x, y):
        super().__init__(random.randint(10001, 20001), Object.image_menu_spr_title, x, y)

class HubOnlineViewer(Object):
    def __init__(self, x, y):
        self.font = Object.font_super_text
        self.online = 0
        self.image = self.font.render(f"Hub ONLINE: {self.online} / 2", False, (255, 255, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.position = Vector2(x, y)
        self.start_time = time.time()
        super().__init__(random.randint(10001, 20001), self.image, self.position[0], self.position[1])
    def tick(self):
        super().tick()
        if time.time()-self.start_time>=3:
            self.image = self.font.render(f"Hub ONLINE: {self.online} / 2", False, (255, 255, 255))
            request = create_request("online", None, client_id)
            request_sender(request)
            self.start_time = time.time()
    def set_online(self, value):
        self.online = value

class HubEscapeText(Object):
    def __init__(self, x, y):
        self.font = Object.font_small_text
        self.image = self.font.render(f"ESC BUTTON - EXIT", False, (255, 255, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.position = Vector2(x, y)
        super().__init__(random.randint(10001, 20001), self.image, self.position[0], self.position[1])

class ErrorDisconnectText(Object):
    def __init__(self, x, y):
        self.font = Object.font_super_text
        self.online = 0
        self.image = self.font.render(f":(", False, (255, 255, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.position = Vector2(x, y)
        super().__init__(random.randint(10001, 20001), self.image, self.position[0], self.position[1])

class ErrorDisconnectGameStartedText(Object):
    def __init__(self, x, y):
        self.font = Object.font_super_text
        self.online = 0
        self.image = self.font.render(f"Game started. Try again later. :)", False, (255, 255, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.position = Vector2(x, y)
        super().__init__(random.randint(10001, 20001), self.image, self.position[0], self.position[1])

class Player(Object):
    def __init__(self, id, x, y):
        super().__init__(id, Object.image_game_spr_churka, x, y)

class Menu(Scene):
    def __init__(self):
        super().__init__()
        menu_start = MenuStart(640, 360)
        menu_start.set_scale(80, 80)
        menu_title = MenuTitle(640, 150)
        menu_title.set_scale(8, 8)
        button_play = ButtonPlay(640, 360)
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
        hub_online_viewer = HubOnlineViewer(640, 100)
        hub_escape_text = HubEscapeText(120, 700)
        self.objects.append(hub_online_viewer)
        self.objects.append(hub_escape_text)
    def tick(self):
        game_renderer.screen.fill((0, 0, 0))
        super().tick()

class Game(Scene):
    def __init__(self):
        super().__init__()
        self.last_ticks = 0
    def tick(self):
        game_renderer.screen.fill((125, 125, 125))
        super().tick()
        if self.ticks-self.last_ticks>16:
            self.get_objects()
            self.last_ticks = self.ticks
    def get_objects(self):
        request = create_request("objects", None, client_id)
        request_sender(request)

class ErrorDisconnect(Scene):
    def __init__(self):
        super().__init__()
        error_disconnect_text = ErrorDisconnectText(640, 360)
        self.objects.append(error_disconnect_text)
    def setup(self):
        print("Error. Can't connect to the server")
    def tick(self):
        game_renderer.screen.fill((0, 0, 0))
        super().tick()

class ErrorDisconnectGameStarted(Scene):
    def __init__(self):
        super().__init__()
        error_disconnect_game_started_text = ErrorDisconnectGameStartedText(640, 360)
        self.objects.append(error_disconnect_game_started_text)
    def setup(self):
        print("Error. Can't connect to the server. Game started.")
    def tick(self):
        game_renderer.screen.fill((0, 0, 0))
        super().tick()
        if True in pygame.mouse.get_pressed():
            print("switched to menu scene")
            game_renderer.set_scene(0)

def main():
    global screen, clock, fps, running, menu, hub, game
    clock = pygame.time.Clock()
    fps = 60
    running = True
    menu = Menu()
    hub = Hub()
    game = Game()
    error_disconnect = ErrorDisconnect()
    error_disconnect_game_started = ErrorDisconnectGameStarted()
    game_renderer.add_scene(menu)
    game_renderer.add_scene(hub)
    game_renderer.add_scene(game)
    game_renderer.add_scene(error_disconnect)
    game_renderer.add_scene(error_disconnect_game_started)
    game_renderer.set_scene(current_scene)
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
            failed_disconnect_attempts += 1
            if failed_disconnect_attempts >= 5:
                print("emergency exit")
                running = False
            request = create_request("disconnect", id=client_id)
            request_sender(request)
        if event.type == pygame.MOUSEWHEEL:
            if event.y == 1 and not camera_locked:
                camera_offset_z += 1
            elif event.y == -1 and not camera_locked:
                camera_offset_z -= 1
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_TAB and not camera_locked:
                camera_offset_x = 0
                camera_offset_y = 0
                camera_offset_z = 0
            elif event.key == pygame.K_ESCAPE and game_renderer.current_scene == 1:
                request = create_request("leave_hub", None, client_id)
                request_sender(request)
                
    game_renderer.tick()
    pygame.display.flip()
    delta_update()
    clock.tick(fps)
s.close()
pygame.quit()
sys.exit()
