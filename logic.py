import pygame
import copy
import math
import random
import time
import socket
import json
import utils
import threading
import struct
from modules.get_name_mc_skin import get_namemc_skins
from modules.get_pygame_skin import get_pygame_skin
from typing import Any, Optional, List, Tuple

def parse_stacked_json(data):
    decoder = json.JSONDecoder()
    pos = 0
    results = []
    
    # Strip leading/trailing whitespace once
    data = data.strip()
    
    while pos < len(data):
        try:
            # Decode one object and get the end position
            obj, pos_end = decoder.raw_decode(data, pos)
            results.append(obj)
            pos = pos_end
            
            # Skip any whitespace between objects to avoid DecodeErrors
            while pos < len(data) and data[pos].isspace():
                pos += 1
                
        except json.JSONDecodeError:
            # Handle or break if malformed data is found
            break
            
    return results

def read_string_in_chunks(text, chunk_size):
    """
    Разбивает строку на части (чанки) указанного размера.
    """
    # range(start, stop, step)
    for start_index in range(0, len(text), chunk_size):
        # Делаем срез от start_index до start_index + chunk_size
        chunk = text[start_index:start_index + chunk_size]
        yield chunk # Используем yield для создания генератора

def recvall(self, length):
    packet_header = self.recv(4)
    if not packet_header:
        return None
    packet_len = struct.unpack('>I', packet_header)[0]
    #print(packet_len)
    
    packet_data = b""
    
    while len(packet_data) < packet_len:
        raw_header = self.recv(4)
        if not raw_header: return None
        msg_len = struct.unpack('>I', raw_header)[0]

        # Read exactly msg_len bytes for the body

        data = b""
        while len(data) < msg_len:
            packet = self.recv(msg_len - len(data))
            if not packet: break
            data += packet
        #print(data)
        packet_data += data
    return packet_data

socket.socket.recvall = recvall


class Logger:
    def __init__(self, console):
        self.console = console
    def print(self, *text, is_error=False):
        print("".join(str(text)))
        self.console.print("".join(str(text)), is_error)

class Console:
    def __init__(self, game, screen_width, FPS):
        self.game = game
        self.screen_width = screen_width
        self.FPS = FPS
        self.from_y = -400
        self.to_y = 0
        self.length = abs(self.from_y-self.to_y)
        self.height = self.length
        self.surface = pygame.Surface((self.screen_width, self.height))
        self.surface.fill("black")
        self.surface.set_alpha(128)
        self.is_enabled = False
        self.x = 0
        self.y = self.from_y
        self.time_to_open = 0.5
        self.speed = self.length/self.time_to_open
        self.is_stopped = True
        self.offset_y = 0
        self.text = ""
        self.command_line = "> "
        self.font = pygame.font.SysFont("Ariel", 30)
        self.command_line_text = self.font.render(self.command_line, True, "white")
        self.command_line_position_offset = [20, -10]
        self.command_line_position = [0+self.command_line_position_offset[0], self.length-self.command_line_text.get_height()+self.command_line_position_offset[1]]
        self.symbol_box_size = (10, self.command_line_text.get_height())
        self.symbol_box_is_visible = True
        self.symbol_box_hiding_time = 60
        self.max_count_symbols = 80
        self.column = self.text.count("\n")
        self.max_console_column_size = (self.length-self.font.get_linesize())//self.font.get_linesize()
        self.colors = {
            "$r": "red",
            "$o": "orange",
            "$y": "yellow",
            "$g": "green",
            "$a": "aqua",
            "$b": "blue",
            "$p": "purple",
            "$w": "white"
        }
        self.commands = utils.read_file(utils.path("settings/commands.json"))

    def print(self, text, is_error=False):
        i = len(text) // self.max_count_symbols
        for i in range(i):
            text = text[:i*self.max_count_symbols] + "\n$g" + text[i*self.max_count_symbols:]

        if text[:2] == "('" and text[-1] == ")":
            text = text[2:len(text)-1]

        if is_error is True:
            text = "$r" + str(text) + "$w" + "\n"
        else:
            text = "$g" + text + "$w" + "\n"

        self.text += text

        self.column = self.text.count("\n")

    def toggle(self):
        self.is_enabled = not self.is_enabled
    def show(self, screen):
        screen.blit(self.surface, [self.x, self.y])
        lines = self.text.split("\n")
        flipped_lines = lines[::-1]
        for i, line in enumerate(flipped_lines[len(lines)-self.column:len(lines)-self.column+self.max_console_column_size]):
            line_surface = self.font.render(line, True, "white")
            line_surface = pygame.Surface(line_surface.get_size())
            line_surface.convert_alpha()
            line_surface.set_colorkey("black")
            color = ""
            color_string_is_started = False
            current_line_width = 0
            for char in line:
                if char == "$":
                    color_string_is_started = True
                    color += char
                elif color_string_is_started and char != "$":
                    color += char
                    color_string_is_started = False
                else:
                    color = color[len(color) - 2:]
                    if color == "":
                        color = "$w"
                    char_surface = self.font.render(char, True, self.colors[color])
                    char_surface.convert_alpha()
                    char_surface.set_colorkey("black")
                    line_surface.blit(char_surface, [current_line_width, 0])
                    current_line_width += char_surface.get_width()

            screen.blit(line_surface, (self.x+self.command_line_position[0], self.y+self.command_line_position[1]-(i+1)*self.font.get_linesize()-self.offset_y))
        screen.blit(self.command_line_text, [self.x+self.command_line_position[0], self.y+self.command_line_position[1]])
        if self.game.ticks % self.symbol_box_hiding_time == 0:
            self.symbol_box_is_visible = not self.symbol_box_is_visible
        if self.symbol_box_is_visible:
            pygame.draw.rect(screen, "white", [self.x+self.command_line_position[0]+self.command_line_text.get_width()+self.symbol_box_size[0], self.y+self.command_line_position[1], self.symbol_box_size[0], self.symbol_box_size[1]])
    def update(self, events):
        if self.is_enabled == True:
            self.is_stopped = False

            for event in events:
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_RETURN:
                        self.text += self.command_line[2:] + "\n"


                        parameters = self.command_line[2:].split(" ")
                        command = parameters[0]
                        args = parameters[1:]

                        new_args = []

                        for arg in args:
                            try:
                                new_arg = int(arg)
                                new_arg = str(arg)
                            except:
                                new_arg = "'" + arg + "'"
                            new_args.append(new_arg)

                        if command in self.commands["Commands"]:
                            command_function = "\n".join(self.commands["Commands"][command])
                            skobka_index1 = command_function.rfind("(")
                            skobka_index2 = command_function.rfind(")")
                            command_function = command_function[:skobka_index1+1] + str(",".join(new_args)) + command_function[skobka_index2:]
                            exec(command_function, {"game":self.game})
                        else:
                            self.print("Command not found", True)


                        self.command_line = "> "
                        self.command_line_text = self.font.render(self.command_line, True, "white")
                    elif event.key == pygame.K_UP:
                        self.column -= 1
                    elif event.key == pygame.K_DOWN:
                        self.column += 1
                    elif event.key != pygame.K_BACKSPACE and event.key != pygame.K_RETURN and len(self.command_line[2:]) < self.max_count_symbols:
                        self.command_line += event.unicode
                        self.command_line_text = self.font.render(self.command_line, True, "white")
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        self.command_line = self.command_line[0:max(2, len(self.command_line)-1)]
                        self.command_line_text = self.font.render(self.command_line, True, "white")
                elif event.type == pygame.MOUSEWHEEL:
                    self.column -= event.y
        if self.from_y < self.to_y:
            if self.is_enabled:
                self.y += self.speed * (1 / self.game.FPS)
            else:
                self.y -= self.speed * (1 / self.game.FPS)
        elif self.from_y > self.to_y:
            if self.is_enabled:
                self.y -= self.speed * (1 / self.game.FPS)
            else:
                self.y += self.speed * (1 / self.game.FPS)

        if abs(self.to_y-self.y) <= self.speed * (1 / self.game.FPS) and self.is_stopped is False:
            self.y = self.to_y
            self.is_stopped = True

        if self.column < 0:
            self.column = 0
        elif self.column > self.text.count("\n"):
            self.column = self.text.count("\n")


# -------------------------------------------------------------------
# Менеджер сетевого взаимодействия (UDP + TCP)
# -------------------------------------------------------------------
class NetworkManager:
    def __init__(self, game: 'Game', ip: Tuple[str, int], fps: int):
        self.game = game
        self.IP = ip
        self.FPS = fps
        self.udp_socket: Optional[socket.socket] = None
        self.tcp_socket: Optional[socket.socket] = None
        self.tcp_thread: Optional[threading.Thread] = None
        self.tcp_events: List[Any] = []
        self.tcp_and_udp_is_company = False
        self.last_packet_time = time.time()
        self.network_checking_time = 60
        self.recv_data_size = 2097152
        self.max_failed_connect_ticks = 60
        self.is_access_to_multiplayer = True

    def initialize_udp(self, session_id: int):
        """Создаёт UDP-сокет при старте игры."""
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setblocking(False)
            self.send_udp_event(["New client", [session_id]])
        except ConnectionRefusedError:
            self.udp_socket = None

    def connect_tcp(self, session_id: int) -> bool:
        """Подключает TCP-сокет и запускает фоновый поток приёма."""
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setblocking(True)
        error_code = self.tcp_socket.connect_ex((self.IP[0], self.IP[1] + 1))
        if error_code == 0:
            self.tcp_thread = threading.Thread(
                target=self._tcp_handler, args=[session_id], daemon=True
            )
            self.tcp_thread.start()
            return True
        self.tcp_socket = None
        return False

    def send_udp_event(self, event: List[Any]):
        """Отправляет одно событие по UDP."""
        if self.udp_socket is None:
            return
        request = {
            "event_bus": [event],
            "ticks": self.game.ticks,
            "session_id": self.game.session_id
        }
        data = json.dumps(request).encode()
        try:
            self.udp_socket.sendto(data, tuple(self.IP))
        except (BrokenPipeError, OSError):
            pass

    def send_udp_batch(self, events: List[Any]):
        """Отправляет пакет из нескольких событий по UDP."""
        if not events or self.udp_socket is None:
            return
        request = {
            "event_bus": events,
            "ticks": self.game.ticks,
            "session_id": self.game.session_id
        }
        data = json.dumps(request).encode()
        try:
            self.udp_socket.sendto(data, tuple(self.IP))
        except (BrokenPipeError, OSError):
            pass

    def receive_udp(self) -> List[Any]:
        """Получает UDP-пакет, парсит и возвращает список событий."""
        if self.udp_socket is None:
            return []
        try:
            data = self.udp_socket.recv(self.recv_data_size)
            packet = data.decode()
            start = packet.find("{")
            end = packet.rfind("}")
            if start == -1 or end == -1:
                return []
            packet = packet[start:end + 1]
            if not packet:
                return []
            response = json.loads(packet)
            self.last_packet_time = time.time()
            return response.get("event_bus", [])
        except (BlockingIOError, OSError, json.JSONDecodeError):
            return []

    def _tcp_handler(self, session_id: int):
        """Фоновый поток для постоянного приёма/отправки по TCP."""
        while True:
            if not self.tcp_and_udp_is_company:
                self.tcp_events.append(["My session id", [session_id]])

            if self.tcp_events:
                try:
                    request = {
                        "event_bus": self.tcp_events,
                        "ticks": self.game.ticks,
                        "session_id": session_id
                    }
                    self.tcp_socket.sendall(json.dumps(request).encode())
                    self.tcp_events = []
                except BrokenPipeError:
                    pass

            try:
                data = self.tcp_socket.recvall(1024)
            except ConnectionResetError:
                data = b""
            if data:
                packet = data.decode()
                try:
                    response = json.loads(packet)
                    if response.get("event_bus"):
                        self.game.tcp_socket_event_bus.extend(response["event_bus"])
                        self.last_packet_time = time.time()
                except json.JSONDecodeError:
                    pass
            time.sleep(1 / self.FPS)


# -------------------------------------------------------------------
# Менеджер сцен
# -------------------------------------------------------------------
class SceneManager:
    def __init__(self, game: 'Game'):
        self.game = game
        self._scenes: dict = {}
        self.current_index = 0

    @property
    def scenes(self):
        return self._scenes

    @property
    def current_scene(self) -> Optional['Scene']:
        if not self._scenes:
            return None
        return list(self._scenes.values())[self.current_index]

    def add_scene(self, scene):
        self._scenes[scene.name] = scene

    def remove_scene(self, name: str):
        self._scenes.pop(name, None)

    def get_scene_by_index(self, index: int = None):
        if index is None:
            index = self.current_index
        return list(self._scenes.values())[index]

    def switch_to(self, index: int):
        self.current_index = index
        scene = self.current_scene
        if scene:
            scene.ticks = 0
            for obj in scene.game_objects.values():
                obj.ticks = 0


# -------------------------------------------------------------------
# Основной класс Game (чистая версия)
# -------------------------------------------------------------------
class Game:
    __slots__ = (
        'screen', 'virtual_screen_size', 'screen_size', 'changed_virtual_screen_position',
        'FPS', 'clock', 'delta_time', 'ticks', 'is_online_mode',
        'logger', 'console', 'is_developer_mode',
        'draw_rects', 'mouse_pos', 'last_mouse_pos',
        'mouse_staying_ticks', 'user_is_afk_ticks', 'user_is_afk',
        'self_player_type_id', 'other_player_type_id', 'map_max_size',
        'online_render_distance', 'session_id', 'game_object_types',
        'my_id', 'lagging_ticks', 'predict_time',
        'last_world_loading_ticks', 'world_loading_timer',
        'compile_mode', 'scene_mgr', 'network',
        'current_event',               # буфер событий, заполняемый сценами
        'tcp_socket_event_bus',        # события, пришедшие по TCP
        'itinerarium', 'itinerarium2',  # прямые ссылки на сокеты (для совместимости)
        "ENVIRONMENT_OS",
        "MAP_MAX_SIZE",
        "chunk_distance_fov",
        "SELF_PLAYER_TYPE_ID",
        "current_scene"
    )

    def __init__(self):
        # Базовые настройки
        self.screen: Optional[pygame.Surface] = None
        self.virtual_screen_size: Optional[Tuple[int, int]] = None
        self.screen_size: Optional[Tuple[int, int]] = None
        self.changed_virtual_screen_position: Optional[List[int]] = None
        self.FPS = 60
        self.clock: Optional[pygame.time.Clock] = None
        self.delta_time = 0.0
        self.ticks = 0
        self.is_online_mode = False
        self.ENVIRONMENT_OS = "Android"
        self.MAP_MAX_SIZE = [-50000, 50000]
        self.chunk_distance_fov = 3
        self.current_scene = 0

        # UI / Отладка
        self.console: Optional[Console] = None       # определён в исходном файле
        self.logger: Optional[Logger] = None         # определён в исходном файле
        self.is_developer_mode = False
        self.draw_rects: List[pygame.Rect] = []

        # Мышь и AFK
        self.mouse_pos = [0, 0]
        self.last_mouse_pos = [0, 0]
        self.mouse_staying_ticks = 0
        self.user_is_afk_ticks = 60
        self.user_is_afk = False

        # Идентификаторы объектов в сети
        self.SELF_PLAYER_TYPE_ID = 0
        self.other_player_type_id = 1
        self.map_max_size = [-50000, 50000, -50000, 50000]
        self.online_render_distance = 300
        self.session_id = random.randint(0, 1000)
        self.game_object_types: dict = {}
        self.my_id: Optional[int] = None
        self.lagging_ticks = 2400
        self.predict_time = 60

        # Загрузка мира
        self.last_world_loading_ticks = 0
        self.world_loading_timer = 600

        # Режим компиляции
        self.compile_mode = "Debug"

        # Менеджеры
        self.scene_mgr = SceneManager(self)
        self.network: Optional[NetworkManager] = None

        # Буферы событий (публичные, используются сценами)
        self.current_event: List[Any] = []
        self.tcp_socket_event_bus: List[Any] = []

        # Сокеты (оставлены для обратной совместимости, если сцены обращаются напрямую)
        self.itinerarium: Optional[socket.socket] = None
        self.itinerarium2: Optional[socket.socket] = None

    # ----------------------------------------------------------------
    # Инициализация
    # ----------------------------------------------------------------
    def setup(self, screen, virtual_screen_size, environment_os, tile_size,
              ip, chunk_distance_fov, clock, game_objects_render_distance,
              compile_mode, fps):
        self.screen = screen
        self.virtual_screen_size = virtual_screen_size
        self.screen_size = screen.get_size()
        self.ENVIRONMENT_OS = environment_os
        self.chunk_distance_fov = chunk_distance_fov
        self.FPS = fps
        self.clock = clock
        self.compile_mode = compile_mode
        self.changed_virtual_screen_position = [0, 0]

        # Сетевой менеджер
        self.network = NetworkManager(self, ip, fps)

        # Консоль и логгер (определены в глобальной области, передаём ссылку на игру)
        self.console = Console(self, virtual_screen_size[0], fps)
        self.logger = Logger(self.console)

        self.screen.fill((255, 255, 255))

    # ----------------------------------------------------------------
    # Сцены (делегированы менеджеру сцен)
    # ----------------------------------------------------------------
    @property
    def scenes(self):
        return self.scene_mgr.scenes

    def get_scene(self, index=None):
        return self.scene_mgr.get_scene_by_index(index)

    def add_scene(self, new_scene):
        self.scene_mgr.add_scene(new_scene)

    def remove_scene(self, scene_name):
        self.scene_mgr.remove_scene(scene_name)

    def change_current_scene(self, index):
        self.scene_mgr.switch_to(index)
        self.current_scene = index
    
    def update_room_label(self, room_label_name):
    	"""Вызывается кнопками для запроса списка комнат."""
    	current_scene = self.get_scene()
    	if current_scene is None:
    		return
    	current_scene.room_label = current_scene.game_objects.get(room_label_name)
    	self.current_event.append(["Get rooms", []])
        

    # ----------------------------------------------------------------
    # Сетевые действия (API, вызываемое сценами/кнопками)
    # ----------------------------------------------------------------
    def join_room(self, room_name, nickname):
        if self.network and self.network.is_access_to_multiplayer:
            self.current_event.append(["Join room", [room_name, nickname]])
            self.change_current_scene(7)   # индекс онлайн-сцены

    def create_room(self):
        if self.network and self.network.is_access_to_multiplayer:
            self.current_event.append(["Create room", [str(random.randint(1, 5))]])
            self.change_current_scene(0)

    def exit_from_room(self, current_scene=None):
        if current_scene is None:
            current_scene = self.get_scene()
        self.clear_scene(current_scene)
        self.change_current_scene(0)
        self.current_event.append(["Leave room", []])

    def clear_scene(self, scene):
        scene.my_player_id = None
        scene.player_game_object_name = None
        scene.current_player_game_object = None
        removing = [obj for obj in scene.game_objects.values() if obj.is_online_mode]
        for obj in removing:
            scene.remove_game_object(obj)

    # ----------------------------------------------------------------
    # Вспомогательные методы
    # ----------------------------------------------------------------
    def get_mouse_pos(self):
        mouse_pos = list(pygame.mouse.get_pos())
        if self.screen_size[0] > self.screen_size[1]:
            virt_w, virt_h = self.virtual_screen_size
        else:
            virt_w, virt_h = self.virtual_screen_size[1], self.virtual_screen_size[0]
        ox = self.changed_virtual_screen_position[0]
        oy = self.changed_virtual_screen_position[1]
        mouse_pos[0] = (mouse_pos[0] - ox) / (self.screen_size[0] - 2 * ox) * virt_w
        mouse_pos[1] = (mouse_pos[1] - oy) / (self.screen_size[1] - 2 * oy) * virt_h
        return mouse_pos

    # ----------------------------------------------------------------
    # Основной такт игры
    # ----------------------------------------------------------------
    def tick(self, delta_time, changed_virtual_screen_position):
        self.delta_time = delta_time
        self.changed_virtual_screen_position = changed_virtual_screen_position

        # 1. Обновляем текущую сцену
        scene = self.get_scene()
        self.draw_rects = []
        scene.tick(delta_time, changed_virtual_screen_position)

        # 2. Консоль
        self.console.show(self.screen)

        # 3. Онлайн-статус
        self.is_online_mode = scene.is_online_mode

        # 4. Мышь и AFK
        self.last_mouse_pos = self.mouse_pos
        self.mouse_pos = self.get_mouse_pos()
        self.mouse_staying_ticks = 0 if self.mouse_pos != self.last_mouse_pos else self.mouse_staying_ticks + 1

        player_ctrl = scene.player_controller_game_object
        ctrl_dir = player_ctrl.direction if player_ctrl else [0, 0]
        self.user_is_afk = (ctrl_dir == [0, 0] and self.mouse_staying_ticks > self.user_is_afk_ticks)

        # 5. Сетевое взаимодействие
        if self.network is not None:
            self._process_network(scene)

        self.ticks += 1

    # ----------------------------------------------------------------
    # Вся сетевая логика, вынесенная из tick
    # ----------------------------------------------------------------
    def _process_network(self, scene):
        nm = self.network

        # Инициализация UDP, если ещё нет
        if nm.udp_socket is None:
            nm.initialize_udp(self.session_id)
            self.itinerarium = nm.udp_socket

        # Попытка TCP‑подключения на 10-м тике
        if self.ticks == 10 and nm.tcp_socket is None:
            if nm.connect_tcp(self.session_id):
                self.logger.print("Подключено успешно!")
                self.itinerarium2 = nm.tcp_socket
            else:
                self.logger.print("Ошибка подключения к TCP", True)
                nm.is_access_to_multiplayer = False

        # Keep‑alive / проверка живости
        if time.time() - nm.last_packet_time > nm.network_checking_time and self.ticks % 60 == 0:
            nm.send_udp_event(["New client", [self.session_id]])

        if self.ticks % 120 == 0:
            nm.send_udp_event(["Client alive", [True]])

        # Запрос ID игрока
        if self.ticks % 60 == 0 and scene.my_player_id is None and scene.is_online_mode:
            nm.send_udp_event(["Get player ID", []])

        # Запрос игровых объектов (при необходимости)
        need_objects = (
            (scene.tilemap is None and self.ticks % 60 == 0)
            or (self.ticks - self.last_world_loading_ticks > self.world_loading_timer and self.user_is_afk)
        )
        if need_objects and scene.is_online_mode and scene.my_player_id is not None:
            nm.send_udp_event(["Get game objects", []])
            self.last_world_loading_ticks = self.ticks

        # Запрос изменений
        if scene.is_online_mode:
            self.current_event.append(["Get changes", [self.ticks]])

        # Запрос тайлмапа, если ещё не загружен
        if (scene.is_online_mode and scene.tilemap is not None
                and self.ticks % 60 == 0 and not scene.tilemap.first_load):
            self.current_event.append(["Get tilemap", []])

        # Отправка накопленных событий
        if self.current_event:
            nm.send_udp_batch(self.current_event)
            self.current_event = []

        # Приём UDP‑пакетов
        events = nm.receive_udp()

        # Добавление TCP‑событий
        if self.tcp_socket_event_bus:
            events.extend(self.tcp_socket_event_bus)
            self.tcp_socket_event_bus = []

        # Обработка всех полученных событий
        for event in events:
            if len(str(event[1])) < 100:
                self.logger.print(event[0], event[1])
            self._process_server_event(event, scene)

    # ----------------------------------------------------------------
    # Единый метод обработки событий от сервера
    # ----------------------------------------------------------------
    def _process_server_event(self, event, scene):
        """Оригинальная логика разбора событий, полностью перенесена из старого tick."""
        event_name = event[0]
        event_data = event[1]

        if event_name == "Your ID":
            self.my_id = event_data[0]

        elif event_name == "Your player ID":
            scene.my_player_id = event_data[0]

        elif event_name == "Add game object":
            if event_data[0] == "Player":
                game_object = copy.copy(self.game_object_types["PeaShooter"])
            elif event_data[0] == "Cube":
                game_object = copy.copy(self.game_object_types["Cube"])
            game_object.name = "Z" + str(event_data[1])
            game_object.id = event_data[1]
            game_object.position = event_data[2]
            game_object.scene = scene
            game_object.camera = scene.current_camera
            game_object.is_online_mode = True
            game_object.setup()
            scene.add_game_object(game_object)

        elif event_name == "Your condition of the room":
            self.ticks = event[2] if len(event) > 2 else self.ticks
            live_objects = []
            for obj_data in event_data[0]["Game objects"]:
                obj_type = obj_data[0]
                obj_name = "Z" + str(obj_data[1])
                obj_id = obj_data[1]
                obj_pos = obj_data[2]
                live_objects.append(obj_name)
                if obj_name not in scene.game_objects:
                    if obj_type == "Player":
                        go = copy.copy(self.game_object_types["PeaShooter"])
                        go.name = obj_name
                        go.id = obj_id
                        go.position = obj_pos
                        go.scene = scene
                        go.camera = scene.current_camera
                        go.is_online_mode = True
                        go.setup()
                        scene.add_game_object(go)
                else:
                    scene.game_objects[obj_name].id = obj_id
                    scene.game_objects[obj_name].position = obj_pos
            # Удаление лишних
            for go in list(scene.game_objects.values()):
                if go.is_online_mode and go.name not in live_objects:
                    scene.remove_game_object(go)

        elif event_name == "Game object moved":
            name = "Z" + str(event_data[0])
            if name in scene.game_objects:
                scene.game_objects[name].position = event_data[1]

        elif event_name == "Your rooms":
            if "JoinRoomRoomLabel" in scene.game_objects:
                scene.game_objects["JoinRoomRoomLabel"].update_room_label(event_data[0])

        elif event_name == "Game object state changed":
            self._handle_game_object_state_changed(event_data, scene)

        elif event_name == "Add room":
            if "JoinRoom" in self.scenes:
                label = self.scenes["JoinRoom"].game_objects.get("JoinRoomRoomLabel")
                if label:
                    label.update_room_label(event_data)

        elif event_name == "Your game objects":
            #print(event_data)
            self._handle_your_game_objects(event_data, scene)

        elif event_name == "Leave room now":
            self.exit_from_room()

        elif event_name == "Your tilemap":
            if scene.tilemap is not None:
                TileMap.config_tilemaps["TileMaps"][scene.tilemap.tilemap_name] = event_data[0]
                scene.tilemap.first_load = True
                scene.tilemap.setup()

        elif event_name == "Tcp and Udp detected":
            if self.network:
                self.network.tcp_and_udp_is_company = True

        elif event_name == "Your changes":
            for game_event in event_data[0]:
                ge_name = game_event[0]
                ge_data = game_event[1]
                if ge_name == "Game object state changed":
                    param = ge_data[0]
                    obj_id = ge_data[1]
                    scene_id = "Z" + str(obj_id)
                    if scene_id in scene.game_objects:
                        obj = scene.game_objects[scene_id]
                        if param == "position":
                            obj.position = ge_data[3]

        elif event_name == "Your ticks":
            self.ticks = event_data[0]

    def _handle_game_object_state_changed(self, data, scene):
        type_change = data[0]
        obj_id = data[1]
        obj_pos = data[3]
        obj_type_id = data[4]

        if type_change == 2:
            # Тип игрока изменился (например, стал зомби)
            if obj_type_id == self.self_player_type_id:
                scene.game_objects.pop(scene.current_player_game_object.name, None)
                scene.current_player_game_object.name = "Z" + str(obj_id)
                scene.current_player_game_object.id = obj_id
                scene.game_objects["Z" + str(obj_id)] = scene.current_player_game_object
            elif "Z" + str(obj_id) not in scene.game_objects:
                go = copy.copy(self.game_object_types["PeaShooter"])
                go.name = "Z" + str(obj_id)
                go.id = obj_id
                go.position = obj_pos
                go.scene = scene
                go.camera = scene.current_camera
                go.is_online_mode = True
                go.setup()
                scene.game_objects[go.name] = go
        tag = "Z" + str(obj_id)
        if tag in scene.game_objects:
            scene.game_objects[tag].set_position(obj_pos)

    def _handle_your_game_objects(self, data: object, scene: object) -> None:
        event_data = data[0]
        game_objects_ids = event_data[0]
        game_objects_data = event_data[1]
        scene.game_objects_data = event_data
        #print("EVENT DATA", event_data, "DATA", data)
        if scene.my_player_id is not None:
            try:
                #print(data[0][0][1][str(scene.my_player_id)])
                try:
                    my_type = game_objects_data[str(scene.my_player_id)][2]
                except TypeError:
                    return
            except KeyError:
                self.change_current_scene(0)
                return
        else:
            my_type = None

        # Создание своего игрока, если ещё нет
        if (str(scene.my_player_id) in game_objects_data
                and "Z" + str(scene.my_player_id) not in scene.game_objects):
            if my_type == "Player":
                go = copy.copy(self.game_object_types["MinecraftSkin"])
                go.nickname = game_objects_data[str(scene.my_player_id)][3]
                go.inventory = scene.player_inventory
                scene.player_inventory.player = go
                scene.player_hp.player = go
            go.name = "Z" + str(scene.my_player_id)
            go.id = scene.my_player_id
            go.type_id = self.SELF_PLAYER_TYPE_ID
            go.set_position(game_objects_data[str(scene.my_player_id)][0])
            go.velocity = game_objects_data[str(scene.my_player_id)][1]
            go.scene = scene
            go.camera = scene.current_camera
            go.is_online_mode = True
            go.mode = "Player"
            go.setup()
            scene.add_game_object(go)

        # Остальные объекты
        for obj_id in game_objects_ids:
            tag = "Z" + str(obj_id)
            if tag not in scene.game_objects:
                obj_type = game_objects_data[str(obj_id)][2]
                if obj_type == "Player":
                    go = copy.copy(self.game_object_types["MinecraftSkin"])
                    go.mode = "Player"
                    go.nickname = game_objects_data[str(obj_id)][3]
                    go.inventory_data = game_objects_data[str(obj_id)][4]
                    go.hand_item_type = game_objects_data[str(obj_id)][5]
                    go.hp = game_objects_data[str(obj_id)][6]
                    skin_id = get_namemc_skins(go.nickname)[0]
                    skin_surface = get_pygame_skin(skin_id)
                    skin_surface.convert_alpha()
                    skin_head_surface = skin_surface.subsurface([8, 8, 8, 8])
                    skin_head_surface = pygame.transform.scale(skin_head_surface, (go.width, go.height))
                    skin_head_surface.convert_alpha()
                    skin_head_second_floor = skin_surface.subsurface([48, 8, 8, 8])
                    skin_head_second_floor = pygame.transform.scale(skin_head_second_floor, (go.width, go.height))
                    skin_head_second_floor.convert_alpha()
                    skin_head_second_floor.set_colorkey("black")
                    skin_head_surface.blit(skin_head_second_floor, [0, 0])
                    go.animation_frame_images[go.state][go.animation_current_frame] = skin_head_surface
                elif obj_type == "Zombie":
                    go = copy.copy(self.game_object_types["Zombie"])
                    go.mode = "Zombie"
                    go.nickname = game_objects_data[str(obj_id)][3]
                    go.inventory_data = game_objects_data[str(obj_id)][4]
                    go.hand_item_type = game_objects_data[str(obj_id)][5]
                    go.hp = game_objects_data[str(obj_id)][6]
                elif obj_type == "Item":
                    go = Item()
                    items_anim = {0: "Camera", 1: "Pickaxe", 2: "Sword", 3: "Gun", 4: "Coin"}
                    go.animation_name = items_anim.get(game_objects_data[str(obj_id)][3], "Camera")
                    go.item_type = game_objects_data[str(obj_id)][3]
                elif obj_type == "Tilemap":
                    TileMap.config_tilemaps["TileMaps"].update({f"Z_{obj_id}": []})
                    go = TileMap()
                    go.animation_name = "Camera"
                    go.tilemap_name = f"Z_{obj_id}"
                    scene.tilemap = go
                elif obj_type == "Bullet":
                    go = Bullet()
                elif obj_type == "Bariga":
                    go = Bariga()
                    go.required_item_type = game_objects_data[str(obj_id)][3]
                    go.required_quantity = game_objects_data[str(obj_id)][4]
                    go.given_item_type = game_objects_data[str(obj_id)][5]
                go.name = "Z" + str(obj_id)
                go.id = obj_id
                go.set_position(game_objects_data[str(obj_id)][0])
                go.velocity = game_objects_data[str(obj_id)][1]
                go.type_id = obj_type
                go.scene = scene
                go.camera = scene.current_camera
                go.is_online_mode = True
                go.setup()
                scene.add_game_object(go)
            else:
                # Обновление существующего объекта
                obj = scene.game_objects[tag]
                obj.set_position(game_objects_data[str(obj_id)][0])
                obj.velocity = game_objects_data[str(obj_id)][1]
                obj_type = game_objects_data[str(obj_id)][2]
                if obj_type == "Player":
                    obj.nickname = game_objects_data[str(obj_id)][3]
                    obj.inventory_data = game_objects_data[str(obj_id)][4]
                    obj.hand_item_type = game_objects_data[str(obj_id)][5]
                    obj.hp = game_objects_data[str(obj_id)][6]
                    skin_id = get_namemc_skins(obj.nickname)[0]
                    skin_surface = get_pygame_skin(skin_id)
                    skin_surface.convert_alpha()
                    skin_head_surface = skin_surface.subsurface([8, 8, 8, 8])
                    skin_head_surface = pygame.transform.scale(skin_head_surface, (obj.width, obj.height))
                    skin_head_surface.convert_alpha()
                    skin_head_second_floor = skin_surface.subsurface([48, 8, 8, 8])
                    skin_head_second_floor = pygame.transform.scale(skin_head_second_floor, (obj.width, obj.height))
                    skin_head_second_floor.convert_alpha()
                    skin_head_second_floor.set_colorkey("black")
                    skin_head_surface.blit(skin_head_second_floor, [0, 0])
                    obj.animation_frame_images[obj.state][obj.animation_current_frame] = skin_head_surface
                elif obj_type == "Tilemap":
                    if obj.first_load:
                        for edit in game_objects_data[str(obj_id)][3]:
                            obj.edit_chunk(edit[0], edit[1])
                elif obj_type == "Bariga":
                    obj.required_item_type = game_objects_data[str(obj_id)][3]
                    obj.required_quantity = game_objects_data[str(obj_id)][4]
                    obj.given_item_type = game_objects_data[str(obj_id)][5]




class Scene:
    __slots__ = ["type", "name", "game_objects", "entities", "walls", "sprite_group", "game", "current_camera", "current_camera_name", "current_player_game_object", "player_game_object_name", "player_controller_game_object", "player_controller_game_object_name", "is_online_mode", "my_player_id", "tilemap_name", "tilemap", "not_animated", "camera", "game_objects_", "room_label_name", "room_label", "game_objects_data", "player_inventory", "player_inventory_name", "items", "player_hp", "player_hp_name", "ticks"]
    def __init__(self):        
        self.type = None
        
        self.name = None
        
        self.game_objects = {}
        
        self.game_objects_ = []
        
        self.entities = {}
        
        self.walls = {}
        
        self.items = []
        
        self.sprite_group = pygame.sprite.Group()
        
        self.game = None

        self.current_camera = None
        
        self.current_camera_name = None
        
        self.current_player_game_object = None
        
        self.player_game_object_name = None
        
        self.player_controller_game_object = None
        
        self.player_controller_game_object_name = None
        
        self.is_online_mode = False
        
        self.my_player_id = None
        
        self.tilemap_name = None
        
        self.tilemap = None
        
        self.not_animated = True
        
        self.camera = None
        
        self.room_label_name = None
        
        self.room_label = None
        
        self.game_objects_data = [[], {}]
        
        self.player_inventory = None
        
        self.player_inventory_name = None
        
        self.player_hp = None
        
        self.player_hp_name = None
        
        self.ticks = 0

    def setup(self):
        if self.player_controller_game_object_name:
            self.player_controller_game_object = self.game_objects[self.player_controller_game_object_name]
        if self.current_camera_name:
            self.current_camera = self.game_objects[self.current_camera_name]
        if self.tilemap_name:
            self.tilemap = self.game_objects[self.tilemap_name]
        if self.room_label_name:
            self.room_label = self.game_objects[self.room_label_name]
        if self.player_inventory_name is not None:
            self.player_inventory = self.game_objects[self.player_inventory_name]
        if self.player_hp_name is not None:
            self.player_hp = self.game_objects[self.player_hp_name]
        
    def add_game_object(self, new_game_object):
         new_game_object.camera = self.current_camera
         self.game_objects.update({new_game_object.name:new_game_object})
         sorted_keys = sorted(self.game_objects)
         self.game_objects = {key:self.game_objects[key] for key in sorted_keys}

         self.game_objects_.insert(list(self.game_objects.values()).index(new_game_object), new_game_object)
         if isinstance(new_game_object, Entity):
             self.entities.update({new_game_object.name:new_game_object})
             sorted_keys = sorted(self.entities)
             self.entities = {key:self.entities[key] for key in sorted_keys}
         elif isinstance(new_game_object, Wall):
              self.walls.update({new_game_object.name:new_game_object})
              sorted_keys = sorted(self.walls)
              self.walls = {key:self.walls[key] for key in sorted_keys}
              self.sprite_group.add(new_game_object)
         elif isinstance(new_game_object, Item):
            self.items.append(new_game_object)
    def remove_game_object(self, old_game_object):
        if old_game_object.name in self.game_objects:
            self.game_objects.pop(old_game_object.name)
            if isinstance(old_game_object, Entity):
                self.entities.pop(old_game_object.name)
            elif isinstance(old_game_object, Wall):
                self.walls.pop(old_game_object.name)
            elif isinstance(old_game_object, Item):
                self.items.remove(old_game_object)
    def tick(self, delta_time, changed_virtual_screen_position):
            """
            if self.ticks == 0 and self.is_online_mode is True:
                removable_game_objects = []
                for game_object in list(self.game_objects.values()):
                    if isinstance(game_object, TileMap):
                        removable_game_objects.append(game_object)
                for removable_game_object in removable_game_objects:
                    self.remove_game_object(removable_game_object
            """
            if self.ticks % 300 == 0:
                game_objects = list(self.game_objects.values())
                if self.player_inventory not in game_objects and self.player_inventory is not None:
                    self.add_game_object(self.player_inventory)
                if self.player_controller_game_object not in game_objects and self.player_controller_game_object is not None:
                    self.add_game_object(self.player_controller_game_object)
            if self.my_player_id is not None:
                    if "Z"+str(self.my_player_id) in self.game_objects:
                        self.player_game_object_name = "Z"+str(self.my_player_id)
                        self.game_objects[self.player_game_object_name].id = self.my_player_id


            if self.player_game_object_name and self.current_player_game_object is None:
                        self.current_player_game_object = self.game_objects[self.player_game_object_name]
                        self.current_camera.targeting_game_object = self.current_player_game_object
            if self.current_player_game_object is not None and self.player_controller_game_object is not None:
                if self.player_controller_game_object.direction != [0,0]:
                    if isinstance(self.current_player_game_object, Entity):
                        self.current_player_game_object.move(self.player_controller_game_object.direction)
            removing_game_objects = []
            try:
                for game_object in self.game_objects.values():
                    #print("GAME OBJECTS DATA", self.game_objects_data)
                    if str(game_object.id) not in self.game_objects_data[1] and game_object.type_id is not None:
                        removing_game_objects.append(game_object)
                    game_object.tick(delta_time, changed_virtual_screen_position, self.game.screen, self.current_camera)
                    self.game.current_event += game_object.events
                    game_object.events = []
            except RuntimeError as error:
                self.game.logger.print(error)
            for removing_game_object in removing_game_objects:
                self.remove_game_object(removing_game_object)
            self.ticks += 1


class GameObject(pygame.sprite.Sprite):
    __slots__ = (
        "type", "animation_name", "name", "position", "ticks", "last_frame_flip_ticks",
        "animation_ticks", "animation_current_frame", "state", "animation_frame_images",
        "image", "rect", "camera", "scene", "is_only_for_smartphones", "is_online_mode",
        "events", "id", "type_id", "is_gui", "animation_is_alpha", "not_animated",
        "is_rendered", "width", "height", "last_moved_ticks", "screen", "delta_time",
        "changed_virtual_screen_position"
    )

    def __init__(self):
        super().__init__()
        self.type = None
        self.animation_name = None
        self.name = None
        self.position = None
        self.ticks = 0
        self.last_frame_flip_ticks = self.ticks
        self.animation_ticks = {}
        self.animation_current_frame = 0
        self.state = "Default"
        self.animation_frame_images = {}
        self.image = None
        self.rect = None
        self.camera = None
        self.scene = None
        self.is_only_for_smartphones = False
        self.is_online_mode = False
        self.events = []
        self.id = None
        self.type_id = None
        self.is_gui = False
        self.animation_is_alpha = False
        self.not_animated = False
        self.is_rendered = False
        self.width = None
        self.height = None
        self.last_moved_ticks = 0
        # временные атрибуты, устанавливаемые в tick()
        self.screen = None
        self.delta_time = None
        self.changed_virtual_screen_position = None

    def tick(self, delta_time, changed_virtual_screen_position, screen, camera):
        self.screen = screen
        self.delta_time = delta_time
        self.changed_virtual_screen_position = changed_virtual_screen_position
        self.camera = camera

        if not self.is_rendered:
            self.scene.game.draw_rects.append(self.rect)
            self.is_rendered = True

        # Ограничение позиции границами карты (как в исходном коде)
        if self.position[0] > self.scene.game.MAP_MAX_SIZE[1]:
            self.position[0] = self.scene.game.MAP_MAX_SIZE[1]
        elif self.position[0] < self.scene.game.MAP_MAX_SIZE[0]:
            self.position[0] = self.scene.game.MAP_MAX_SIZE[0]
        if self.position[1] > self.scene.game.MAP_MAX_SIZE[1]:
            self.position[1] = self.scene.game.MAP_MAX_SIZE[1]
        elif self.position[1] < self.scene.game.MAP_MAX_SIZE[0]:
            self.position[1] = self.scene.game.MAP_MAX_SIZE[0]

        # Обновление прямоугольника в зависимости от GUI или камеры
        if not self.is_gui:
            self.rect.x = self.position[0] - self.camera.position[0]
            self.rect.y = self.position[1] - self.camera.position[1]
        else:
            self.rect.x = self.position[0]
            self.rect.y = self.position[1]

        # Анимация (пофреймовая, на основе ticks)
        if not self.not_animated:
            if self.ticks - self.last_frame_flip_ticks == self.animation_ticks[self.state][self.animation_current_frame] - 1:
                if self.animation_current_frame + 1 > len(self.animation_frame_images[self.state]) - 1:
                    self.animation_current_frame = 0
                else:
                    pass
                    #self.animation_current_frame += 1
                self.last_frame_flip_ticks = self.ticks

            self.image = self.animation_frame_images[self.state][self.animation_current_frame]
            screen.blit(self.image, self.rect)

        self.ticks += 1

    def setup(self):
        super().__init__()

        config = type(self).config
        animation_info = type(self).config_animations["Animations"][self.animation_name]
        sprites_folder_path = "sprites"

        for animation_state in animation_info:
            self.animation_ticks.update({animation_state: animation_info[animation_state]["Ticks"]})
            self.animation_frame_images.update({animation_state: []})

            for frame_number in range(1, animation_info[animation_state]["Frames"] + 1):
                try:
                    frame_path = f"{sprites_folder_path}/{self.animation_name.lower()}_{animation_state.lower()}{frame_number}.png"
                    frame_image = pygame.image.load(utils.path(frame_path))
                except FileNotFoundError:
                    frame_path = f"{sprites_folder_path}/{self.animation_name.lower()}_{animation_state.lower()}{frame_number}.jpg"
                    frame_image = pygame.image.load(utils.path(frame_path))

                if self.width is not None and self.height is not None:
                    frame_image = pygame.transform.scale(frame_image, (self.width, self.height))

                if self.animation_is_alpha:
                    frame_image = frame_image.convert_alpha()
                else:
                    frame_image = frame_image.convert()

                frame_image.set_colorkey("black")

                self.animation_frame_images[animation_state].append(frame_image)

        self.image = self.animation_frame_images[self.state][self.animation_current_frame]

        if not self.is_gui:
            self.rect = self.image.get_rect(x=self.position[0] - self.camera.position[0],
                                            y=self.position[1] - self.camera.position[1])
        else:
            self.rect = self.image.get_rect(x=self.position[0], y=self.position[1])

    def set_position(self, position):
        self.position = position
        self.last_moved_ticks = self.ticks


class Entity(GameObject):
    __slots__ = [
        "speed",
        "velocity",
        "mode",
        "teleport_zone",
        "hp",
        "font",
        "rendered_text",
        "is_moved",
        "nickname",
        "inventory_data",
        "inventory",
        "hand_item_type",
        "delta_time",
        "touched",
        "old_positions",
        "max_old_positions",
    ]

    def __init__(self, *args):
        super().__init__(*args)
        self.speed = 0
        self.hp = 0
        self.velocity = [0, 0]
        self.mode = "Default"
        self.teleport_zone = [0, 450, 0, 450]
        self.font = None
        self.rendered_text = None
        self.is_moved = False
        self.nickname = None
        self.inventory_data = [0, 0, 0]
        self.inventory = None
        self.hand_item_type = self.inventory_data[0]
        self.delta_time = 0
        self.touched = {
            "left": False,
            "right": False,
            "up": False,
            "down": False,
        }
        self.old_positions = []
        self.max_old_positions = 10

    def setup(self, *args):
        super().setup(*args)
        self.font = pygame.font.SysFont("Arial", 30)
        self.rendered_text = self.font.render(self.nickname, True, "black")

    def tick(self, *args):
        if self.is_online_mode:
            self._handle_online_sync()

        if self.hp <= 0:
            return
        super().tick(*args)

        self._update_visible_chunks()
        self._apply_velocity()
        self._handle_mode_specific_behavior()

    def _handle_online_sync(self):
        """Обработка синхронизации в онлайн-режиме."""
        if self.ticks % 60 == 0:
            last_move_seconds = time.time() - self.last_moved_ticks // 60
            if last_move_seconds > self.scene.game.predict_time:
                self.velocity = [0, 0]

        if self.old_positions:
            first_pos = self.old_positions[0]
            last_pos = self.old_positions[-1]
            if first_pos == last_pos and self.type_id == self.scene.game.SELF_PLAYER_TYPE_ID:
                self._emit_state_change_event()

            if len(self.old_positions) > self.max_old_positions:
                self.old_positions.clear()

        self.old_positions.append(copy.copy(self.position))

    def _emit_state_change_event(self):
        event_data = [
            2,
            self.id,
            self.velocity,
            self.position,
            self.type_id,
            self.nickname,
            self.inventory_data,
            self.hand_item_type,
            self.hp,
        ]
        self.events.append(["Game object state changed", event_data])

    def _update_visible_chunks(self):
        """Обновление видимых чанков."""
        if self.scene.tilemap is None:
            return

        chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
        chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
        visible_chunks = utils.get_visible_chunks(
            chunk_x,
            chunk_y,
            self.scene.game.chunk_distance_fov,
            self.scene.tilemap.map_of_chunks_size,
            self.scene.tilemap.chunks,
        )

        for chunk in visible_chunks:
            chunk_offset_x = (chunk.id % self.scene.tilemap.map_of_chunks_size) * TileMap.chunk_size * TileMap.tile_size
            chunk_offset_y = (chunk.id // self.scene.tilemap.map_of_chunks_size) * TileMap.chunk_size * TileMap.tile_size

            if hasattr(self, "changed_virtual_screen_position"):
                chunk.update(self.delta_time, self.changed_virtual_screen_position)

    def _apply_velocity(self):
        """Применение скорости к позиции."""
        self.position[0] += self.velocity[0] * self.speed * self.delta_time
        self.position[1] += self.velocity[1] * self.speed * self.delta_time

    def _handle_mode_specific_behavior(self):
        """Поведение, зависящее от режима сущности."""
        if self.mode == "Coin":
            self._coin_behavior()
        elif self.mode == "Player" and self.hp > 0:
            self._player_behavior()

    def _coin_behavior(self):
        """Логика монетки: телепортация при касании."""
        if self.ticks % 120 != 0:
            return

        rects = [entity.rect for entity in self.scene.entities.values()]
        rects.remove(self.rect)
        collided_index = self.rect.collidelist(rects)
        if collided_index != -1:
            self.position[0] = random.randint(self.teleport_zone[0], self.teleport_zone[1])
            self.position[1] = random.randint(self.teleport_zone[2], self.teleport_zone[3])

    def _player_behavior(self):
        """Отрисовка ника, предмета в руке и обработка кликов мыши."""
        # Отрисовка ника
        nickname_width = self.rendered_text.get_width()
        nickname_height = self.rendered_text.get_height()
        self.scene.game.screen.blit(
            self.rendered_text,
            [self.rect.x+self.rect.width/2 - nickname_width/2, self.rect.y - nickname_height],
        )

        # Отрисовка предмета в руке
        if self.scene.player_inventory is not None:
            hand_image = self.scene.player_inventory.hand_item_images.get(str(self.hand_item_type))
            if hand_image:
                self.scene.game.screen.blit(hand_image, [self.rect.right, self.rect.centery])

        # Обработка использования предмета (только для собственного игрока)
        if self.type_id != self.scene.game.SELF_PLAYER_TYPE_ID:
            return

        if not pygame.mouse.get_pressed()[0]:
            return

        mouse_pos = self.scene.game.get_mouse_pos()
        if self.hand_item_type == 0:
            return

        if self.scene.player_inventory.inventory_box_rect.collidepoint(mouse_pos):
            return

        if self.scene.game.ENVIRONMENT_OS == "Android":
            if self.scene.player_controller_game_object.touching_zone_box_rect.collidepoint(mouse_pos):
                return

        offset = [
            mouse_pos[0] - self.scene.game.virtual_screen_size[0] / 2,
            mouse_pos[1] - self.scene.game.virtual_screen_size[1] / 2,
        ]
        touched_pos = [self.position[0] + offset[0], self.position[1] + offset[1]]
        self.events.append(["Item used", [touched_pos]])

    def move(self, direction):
        """Перемещение сущности с учётом коллизий."""
        self.velocity = list(direction)
        self._reset_touched_flags()

        # Подготовка списка препятствий (только если карта загружена)
        obstacles = self._get_obstacle_rects()

        # Движение по X
        self._move_axis(0, obstacles)
        # Движение по Y
        self._move_axis(1, obstacles)

        # Отправка события изменения состояния для собственного игрока
        if self.type_id == self.scene.game.SELF_PLAYER_TYPE_ID:
            self._emit_state_change_event()

        self.is_moved = True
        self.velocity = [0, 0]
        self.scene.game.draw_rects.append(self.rect)

    def _reset_touched_flags(self):
        """Сброс флагов касания перед движением."""
        self.touched = {"left": False, "right": False, "up": False, "down": False}

    def _get_obstacle_rects(self):
        """Получение списка прямоугольников препятствий (чанк + объекты)."""
        obstacles = []
        tilemap = self.scene.tilemap
        if tilemap is None or not tilemap.first_load or tilemap.is_online_mode:
            return obstacles

        chunks = []

        angle = math.atan2(self.velocity[1], self.velocity[0]) * (180 / math.pi)

        #print(angle)


        for y in range(3):
            for x in range(3):
                chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1 + x
                chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1 + y
                chunk = utils.get_here_chunk(
                    chunk_x,
                    chunk_y,
                    tilemap.chunks,
                    tilemap.map_of_chunks_size,
                )
                chunks.append(chunk)


        """
        if angle >= -112.5 and angle <= -67.5:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        elif angle >= -157.5 and angle < -112.5:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        elif angle > -67.5 and angle <= -22.5:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        elif angle > -22.5 and angle <= 22.5:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        elif angle > -67.5 and angle < -22.5:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        elif angle > 22.5 and angle <= 67.5:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        elif angle > 67.5 and angle <= 112.5:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        elif angle > 22.5 and angle < 67.5:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        elif angle >= 157.5 and angle < 112.5:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        elif angle > -180 and angle < -157.5 or angle > 157.5 and angle <= 180:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        elif angle > 112.5 and angle < 157.5:
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk1 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size)) - 1
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk2 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size)) + 1
            chunk3 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunk_x = int(self.position[0] // (TileMap.chunk_size * TileMap.tile_size))
            chunk_y = int(self.position[1] // (TileMap.chunk_size * TileMap.tile_size))
            chunk4 = utils.get_here_chunk(
                chunk_x,
                chunk_y,
                tilemap.chunks,
                tilemap.map_of_chunks_size,
            )
            chunks.append(chunk1)
            chunks.append(chunk2)
            chunks.append(chunk3)
            chunks.append(chunk4)
        """

        for chunk in chunks:
            for i, rect in enumerate(chunk.rects):
                rect.x = chunk.rects_position[i][0] - self.camera.position[0]
                rect.y = chunk.rects_position[i][1] - self.camera.position[1]
                obstacles.append(rect)

            for obj in chunk.game_objects.values():
                obstacles.append(obj.rect)

        return obstacles

    def _move_axis(self, axis, obstacles):
        """
        Движение по одной оси (0 - X, 1 - Y) с обработкой коллизий.
        """
        delta = self.speed * self.velocity[axis] * self.delta_time
        self.position[axis] += delta

        # Обновление rect для проверки коллизий
        self.rect.x = self.position[0] - self.camera.position[0]
        self.rect.y = self.position[1] - self.camera.position[1]

        collided_index = self.rect.collidelist(obstacles)
        if collided_index == -1:
            return

        obstacle = obstacles[collided_index]
        if axis == 0:  # X
            if self.velocity[0] > 0 and self.rect.centerx < obstacle.left:
                self.rect.x = obstacle.left - self.rect.width
                self.touched["right"] = True
            elif self.velocity[0] < 0 and self.rect.centerx > obstacle.right:
                self.rect.x = obstacle.right
                self.touched["left"] = True
            self.position[0] = self.rect.x + self.camera.position[0]
        else:  # Y
            if self.velocity[1] > 0 and self.rect.centery < obstacle.top:
                self.rect.y = obstacle.top - self.rect.height
                self.touched["down"] = True
            elif self.velocity[1] < 0 and self.rect.centery > obstacle.bottom:
                self.rect.y = obstacle.bottom
                self.touched["up"] = True
            self.position[1] = self.rect.y + self.camera.position[1]


class Wall(GameObject):
    def update(self, *args):
        """
        mouse_pos = self.scene.game.get_mouse_pos()

        if self.rect.collidepoint(mouse_pos):
            self.position[0] = random.randint(0, 1316)
            self.position[1] = random.randint(0, 718)
        """
        #super().tick(*args)
        self.scene.game.draw_rects.append(self.rect)


class Camera(GameObject):
    """
    Камера, которая может следить за игровыми объектами или оставаться статичной.
    Поддерживает мгновенное и плавное следование.
    """
    __slots__ = (
        "_target_object",
        "_mode",
        "_target_name",
        "_static_position",
        "_focus_zone",
        "_smooth_time",
        "_fps",
        "targeting_game_object_name"
    )

    # Режимы работы камеры
    class Mode:
        STATIC = "Static"
        FOCUS = "Focus_at_game_object"
        SMOOTH_FOCUS = "Slow_focus_at_game_object"

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self._target_object: Optional[GameObject] = None
        self._mode: Optional[str] = None
        self._target_name: Optional[str] = None
        self._static_position: Optional[List[float]] = None
        self._focus_zone: List[int] = [0, 0, 0, 0]
        self._smooth_time: float = 0.5
        self._fps: int = 60

    # Свойства для удобного доступа (сохраняем совместимость с оригинальными именами)
    @property
    def targeting_game_object(self) -> Optional[GameObject]:
        return self._target_object

    @targeting_game_object.setter
    def targeting_game_object(self, value: Optional[GameObject]) -> None:
        self._target_object = value

    @property
    def mode(self) -> Optional[str]:
        return self._mode

    @mode.setter
    def mode(self, value: Optional[str]) -> None:
        self._mode = value

    @property
    def target_game_object_name(self) -> Optional[str]:
        return self._target_name

    @target_game_object_name.setter
    def target_game_object_name(self, value: Optional[str]) -> None:
        self._target_name = value

    @property
    def targeting_position(self) -> Optional[List[float]]:
        return self._static_position

    @targeting_position.setter
    def targeting_position(self, value: Optional[List[float]]) -> None:
        self._static_position = value

    @property
    def focus_zone(self) -> List[int]:
        return self._focus_zone

    @focus_zone.setter
    def focus_zone(self, value: List[int]) -> None:
        self._focus_zone = value

    @property
    def slow_focus_time(self) -> float:
        return self._smooth_time

    @slow_focus_time.setter
    def slow_focus_time(self, value: float) -> None:
        self._smooth_time = value

    @property
    def FPS(self) -> int:
        return self._fps

    @FPS.setter
    def FPS(self, value: int) -> None:
        self._fps = value

    def setup(self) -> None:
        """Находит целевой объект по имени после инициализации сцены."""
        super().setup()
        if self._target_name:
            self._target_object = self.scene.game_objects[self._target_name]

    def tick(self, *args: Any) -> None:
        """Обновляет позицию камеры в зависимости от текущего режима."""
        super().tick(*args)
        if self._mode == self.Mode.FOCUS:
            self._focus_at_game_object()
        elif self._mode == self.Mode.STATIC:
            self._set_static_position()
        elif self._mode == self.Mode.SMOOTH_FOCUS:
            self._smooth_focus_at_game_object()

    def _focus_at_game_object(self) -> None:
        """Мгновенно устанавливает камеру на целевой объект (с учётом размеров экрана)."""
        if not self._target_object:
            return
        target_pos = self._target_object.position
        target_rect = self._target_object.rect
        screen_size = self.scene.game.virtual_screen_size
        new_position = utils.get_camera_position(target_pos, target_rect, screen_size)
        self.set_position(new_position)

    def _smooth_focus_at_game_object(self) -> None:
     """Плавно перемещает камеру к целевому объекту, независимо от FPS."""
     if not self._target_object:
        return
     
     # Целевая позиция камеры (как в мгновенном режиме)
     target_pos = utils.get_camera_position(
        self._target_object.position,
        self._target_object.rect,
        self.scene.game.virtual_screen_size
     )
     
     # Защита от деления на ноль
     if self._smooth_time <= 0:
         self.set_position(target_pos)
         return
        
     # Коэффициент интерполяции за кадр (зависит от delta_time)
     t = min(1.0, self.scene.game.delta_time / self._smooth_time)
     
     new_x = self.position[0] + (target_pos[0] - self.position[0]) * t
     new_y = self.position[1] + (target_pos[1] - self.position[1]) * t
     self.set_position([new_x, new_y])

    def _set_static_position(self) -> None:
        """Устанавливает фиксированную позицию камеры."""
        if self._static_position is not None:
            self.set_position(self._static_position)

    def set_position(self, new_position: List[float]) -> None:
        """Изменяет позицию камеры."""
        self.position = new_position


# Константа для особого блока (196 – сундук/дверь)
SPECIAL_BLOCK_TILE_ID = 196

class Block(GameObject):
    __slots__ = ["id", "tile_id", "chunk_id", "velocity", "type_id", "events",
                 "start_position", "start_rect_position", "camera", "tilemap",
                 "is_closed", "last_is_closed"]

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.id = 0
        self.tile_id = 0
        self.chunk_id = 0
        self.velocity = [0, 0]
        self.type_id = 7
        self.events = []
        self.start_position = [0, 0]
        self.start_rect_position = [0, 0]
        self.camera = None
        self.tilemap = None
        self.is_closed = True
        self.last_is_closed = self.is_closed

    def setup(self, *args: Any) -> None:
        super().setup(*args)
        self.start_position = self.position[:]          # копия списка
        self.start_rect_position = [self.rect.x, self.rect.y]

    def update(self, *args: Any) -> None:
        # ВАЖНО: вызываем именно tick, если родительский метод называется tick
        super().tick(*args)

        # Сохраняем предыдущее состояние ДО возможного переключения
        self.last_is_closed = self.is_closed

        mouse_pos = self.scene.game.get_mouse_pos()
        left_click = pygame.mouse.get_pressed()[0]

        if left_click and self.rect.collidepoint(mouse_pos):
            self.is_closed = not self.is_closed
            if self.is_online_mode:
                self.events.append([
                    "Game object state changed",
                    [3, self.id, self.velocity, self.position, self.type_id, self.chunk_id]
                ])

        # Особое поведение для блока с tile_id == 196
        if self.tile_id == SPECIAL_BLOCK_TILE_ID:
            if self.is_closed != self.last_is_closed:
                if self.is_closed:
                    self.rect.width = self.tilemap.tile_size
                    self.rect.height = self.tilemap.tile_size
                    # Поворот изображения (если нужно) – делайте аккуратно
                    # Например, повернуть кадр анимации на 0 градусов
                    # self.animation_frame_images[self.state][self.animation_current_frame] = \
                    #     pygame.transform.rotate(original, 0)
                else:  # not self.is_closed
                    self.rect.width = 0
                    self.rect.height = 0
                    # Поворот на 90 градусов, если требуется
                    # self.animation_frame_images[self.state][self.animation_current_frame] = \
                    #     pygame.transform.rotate(original, 90)


class Chunk:
    """
    Фрагмент (чанк) тайловой карты.
    Хранит тайлы, стены, игровые объекты и управляет их обновлением.
    """
    __slots__ = (
        "size", "rects", "rects_position", "rects_color", "game_objects",
        "walls", "image", "id", "tiles_ids", "tilemap", "updated_ticks"
    )

    def __init__(self, tilemap: Any, chunk_id: int, image, size: int) -> None:
        """
        Инициализация чанка.

        :param tilemap: Объект тайловой карты.
        :param chunk_id: Уникальный идентификатор чанка.
        :param image: Поверхность (изображение) чанка.
        :param size: Размер чанка (количество тайлов по стороне).
        """
        self.tilemap = tilemap
        self.id = chunk_id
        self.image = image
        self.size = size

        self.rects: List[pygame.Rect] = []
        self.rects_position: List[Tuple[int, int]] = []
        self.rects_color: List[Tuple[int, int, int]] = []
        self.game_objects: Dict[Any, Any] = {}
        self.walls = pygame.sprite.Group()
        self.tiles_ids: List[int] = []

        self.updated_ticks = 0

    def update(self, delta_time: float, offset: tuple[int, int]) -> None:
        """
        Обновляет игровые объекты чанка, если тайловая карта изменилась.

        :param delta_time: Время, прошедшее с предыдущего кадра.
        :param offset: Смещение для отрисовки.
        """
        # Пропускаем обновление, если чанк уже был обновлён в текущем тике
        if self.tilemap.ticks == self.updated_ticks:
            return

        # Обходим все игровые объекты (копия списка, чтобы избежать изменений во время итерации)
        for game_object in list(self.game_objects.values()):
            game_object.update(
                delta_time,
                offset,
                self.tilemap.scene.game.screen,
                self.tilemap.camera
            )
            self.tilemap.scene.game.current_event += game_object.events
            game_object.events = []  # очищаем обработанные события

        # Фиксируем текущий тик как момент последнего обновления
        self.updated_ticks = self.tilemap.ticks


class TileMap(GameObject):
    __slots__ = [
        "tilemap_name",
        "tilemap_size",
        "map_of_chunks_size",
        "chunks",
        "visible_chunks",
        "old_rect_position",
        "player_chunk_x",
        "player_chunk_y",
        "rects_optimization",
        "first_load",
        "objects_tiles_ids",
        "walls_tiles_ids",
    ]

    # Классовые переменные (кэши)
    tiles_images = {}
    chunks_images = {}
    chunk_size = None
    tile_size = None
    game_object_types = {}
    config_tilemaps = {}
    config_tiles = {}
    register_objects_info = {}

    def __init__(self, *args):
        self.tilemap_name = None
        self.tilemap_size = None
        self.map_of_chunks_size = None
        self.chunks = []
        self.visible_chunks = []
        self.old_rect_position = [0, 0]
        self.player_chunk_x = 0
        self.player_chunk_y = 0
        self.rects_optimization = False
        self.first_load = False
        self.objects_tiles_ids = []
        self.walls_tiles_ids = []
        super().__init__(*args)

    def edit_chunk(self, chunk_id, tiles_ids):
        cls = type(self)
        chunk = self.chunks[chunk_id]
        for tile_index, tile_id in enumerate(tiles_ids):
            x = (tile_index % cls.chunk_size) * cls.tile_size
            y = (tile_index // cls.chunk_size) * cls.tile_size
            if tile_id not in self.objects_tiles_ids or tile_id in self.walls_tiles_ids:
                chunk.image.blit(cls.tiles_images[tile_id], (x, y))

    def setup(self):
        super().setup()
        cls = type(self)

        if not self.scene.is_online_mode:
            self.first_load = True

        # Загрузка данных тайлмапа
        tilemap_info = self._load_tilemap_data()
        self._init_dimensions(len(tilemap_info))
        self._load_tile_images()

        # Создание чанков
        self.chunks = []
        self._create_chunks(tilemap_info)

    def _load_tilemap_data(self):
        """Загрузка сырых данных тайлмапа (список ID тайлов)."""
        cls = type(self)
        tilemap_file_name = cls.config_tilemaps["TileMaps"][self.tilemap_name]
        PATH_TO_FOLDER = "tilemaps"

        if not self.is_online_mode:
            file_path = utils.path(
                f"{PATH_TO_FOLDER}/{tilemap_file_name}",
                self.scene.game.ENVIRONMENT_OS,
            )
            tilemap_file_info = utils.read_file(file_path)
            try:
                tilemap_info = list(tilemap_file_info["layers"][0]["data"].split(","))
            except AttributeError:
                tilemap_info = list(tilemap_file_info["layers"][0]["data"])
        else:
            tilemap_info = cls.config_tilemaps["TileMaps"][self.tilemap_name]

        return [int(tile_id) for tile_id in tilemap_info]

    def _init_dimensions(self, tile_count):
        cls = type(self)
        self.tilemap_size = int(math.sqrt(tile_count))
        self.map_of_chunks_size = self.tilemap_size // cls.chunk_size

        self.rect.width = self.map_of_chunks_size * cls.chunk_size * cls.tile_size
        self.rect.height = self.map_of_chunks_size * cls.chunk_size * cls.tile_size

    def _load_tile_images(self):
        """Загрузка изображений тайлов в кэш класса."""
        cls = type(self)
        tiles_info = cls.config_tiles["Tiles"]

        self.objects_tiles_ids = []
        self.walls_tiles_ids = []
        alpha_tiles_ids = []

        for tile_id_str, tile_type in tiles_info.items():
            tile_id = int(tile_id_str)
            is_animated = True

            if tile_type in cls.game_object_types:
                # Создаём временный объект для получения изображения
                game_object = copy.copy(cls.game_object_types[tile_type])
                game_object.camera = self.camera
                game_object.position = [0, 0]
                game_object.setup()
                image = game_object.image
                self.objects_tiles_ids.append(tile_id)

                if isinstance(game_object, Wall):
                    self.walls_tiles_ids.append(tile_id)

                if not cls.game_object_types[tile_type].not_animated:
                    is_animated = False
            else:
                try:
                    image = pygame.image.load(
                        utils.path(f"sprites/{tile_type}.png")
                    ).convert_alpha()
                except FileNotFoundError:
                    image = pygame.image.load(
                        utils.path(f"sprites/{tile_type}.jpg")
                    ).convert()
                alpha_tiles_ids.append(tile_id)

            if is_animated:
                cls.tiles_images[tile_id] = image
            else:
                cls.tiles_images[tile_id] = image

    def _create_chunks(self, tilemap_info):
        """Создание всех чанков и наполнение их тайлами и объектами."""
        cls = type(self)
        total_chunks = self.map_of_chunks_size ** 2

        for chunk_id in range(total_chunks):
            chunk_image = pygame.Surface(
                (cls.chunk_size * cls.tile_size, cls.chunk_size * cls.tile_size)
            )
            chunk = Chunk(self, chunk_id, chunk_image, cls.chunk_size)
            self.chunks.append(chunk)

            # Извлечение ID тайлов для текущего чанка
            tiles_ids = self._extract_chunk_tile_ids(chunk_id, tilemap_info)
            chunk.tiles_ids = tiles_ids

            # Определение необходимости альфа-канала
            self._configure_chunk_surface(chunk, chunk_image)

            # Отрисовка тайлов и создание игровых объектов
            self._fill_chunk(chunk, tiles_ids)

    def _extract_chunk_tile_ids(self, chunk_id, tilemap_info):
        """Извлечение списка ID тайлов, принадлежащих чанку."""
        cls = type(self)
        chunk_x = chunk_id % self.map_of_chunks_size
        chunk_y = chunk_id // self.map_of_chunks_size
        tiles_ids = []

        for i in range(cls.chunk_size):
            start = (
                chunk_x * cls.chunk_size
                + chunk_y * (cls.chunk_size ** 2) * self.map_of_chunks_size
                + self.tilemap_size * i
            )
            end = start + cls.chunk_size
            tiles_ids.extend(tilemap_info[start:end])

        return tiles_ids

    def _configure_chunk_surface(self, chunk, chunk_image):
        """Настройка альфа-канала для поверхности чанка."""
        cls = type(self)
        # Проверка, есть ли в чанке хотя бы один тайл с альфой
        has_alpha = any(
            tile_id in cls.tiles_images and cls.tiles_images[tile_id].get_flags() & pygame.SRCALPHA
            for tile_id in chunk.tiles_ids
        )
        if has_alpha:
            chunk_image.convert_alpha()
        else:
            chunk_image.convert()

    def _fill_chunk(self, chunk, tiles_ids):
        """Отрисовка тайлов на чанке и создание игровых объектов."""
        cls = type(self)
        tiles_info = cls.config_tiles["Tiles"]
        register_objects_info = cls.register_objects_info["Register_objects"]

        # Определение самого частого тайла для фона
        most_frequent_tile_id = self._get_most_frequent(tiles_ids)

        for tile_index, tile_id in enumerate(tiles_ids):
            x = (tile_index % cls.chunk_size) * cls.tile_size
            y = (tile_index // cls.chunk_size) * cls.tile_size

            # Отрисовка тайла
            if (
                tile_id not in self.objects_tiles_ids
                or tile_id in self.walls_tiles_ids
            ):
                chunk.image.blit(cls.tiles_images[tile_id], (x, y))
            else:
                chunk.image.blit(cls.tiles_images[most_frequent_tile_id], (x, y))

            # Создание игрового объекта, если тайл является объектом
            if tile_id in self.objects_tiles_ids:
                if self.rects_optimization:
                    self._create_optimized_objects(chunk, tile_index, tiles_ids)
                else:
                    self._create_single_object(chunk, tile_index, tile_id)

    def _get_most_frequent(self, items):
        """Возвращает наиболее часто встречающийся элемент списка."""
        frequency = {}
        for item in items:
            frequency[item] = frequency.get(item, 0) + 1
        return max(frequency, key=frequency.get)

    def _create_single_object(self, chunk, tile_index, tile_id):
        """Создание одиночного игрового объекта по тайлу."""
        cls = type(self)
        tiles_info = cls.config_tiles["Tiles"]
        register_objects_info = cls.register_objects_info["Register_objects"]

        chunk_x = chunk.id % self.map_of_chunks_size
        chunk_y = chunk.id // self.map_of_chunks_size

        x = (
            (tile_index % cls.chunk_size) * cls.tile_size
            + chunk_x * cls.chunk_size * cls.tile_size
        )
        y = (
            (tile_index // cls.chunk_size) * cls.tile_size
            + chunk_y * cls.chunk_size * cls.tile_size
        )

        type_name = tiles_info[str(tile_id)]
        arguments = copy.copy(register_objects_info[type_name])
        arguments.pop("Type", None)
        arguments.update(
            {
                "Name": f"{self.tilemap_name}{chunk.id}{tile_index}",
                "Position": [x, y],
            }
        )

        game_object = copy.copy(cls.game_object_types[type_name])
        self._setup_game_object(game_object, arguments)
        game_object.tile_id = tile_id
        game_object.id = tile_index
        game_object.chunk_id = chunk.id

        if isinstance(game_object, Wall):
            chunk.walls.add(game_object)
            chunk.rects_position.append([x, y])
            chunk.rects.append(pygame.Rect(x, y, cls.tile_size, cls.tile_size))
        else:
            chunk.game_objects[str(game_object.id)] = game_object

    def _create_optimized_objects(self, chunk, start_index, tiles_ids):
        """
        Оптимизированное создание объектов путём объединения смежных тайлов
        одного типа в один прямоугольник (логика сохранена как в оригинале).
        """
        cls = type(self)
        tiles_info = cls.config_tiles["Tiles"]
        register_objects_info = cls.register_objects_info["Register_objects"]

        # В оригинале используется переменная objects_tiles_ids, но она не определена.
        # Скорее всего, подразумевалась self.objects_tiles_ids.
        # Исправляем на self.objects_tiles_ids.
        obj_tiles_ids = self.objects_tiles_ids

        # Пропускаем, если этот тайл уже обработан как часть объединённого прямоугольника
        # (в оригинале это делается через united_tiles_indexs, но логика неполная).
        # Чтобы не сломать, оставляем оригинальный алгоритм "как есть", но с исправлением имени переменной.
        # Однако в оригинале алгоритм выглядит незавершённым и потенциально ошибочным.
        # Мы сохраним его точь-в-точь, чтобы не нарушить работу.
        united_tiles_indexs = []
        tile_id = tiles_ids[start_index]

        point_x1 = start_index
        point_x2 = point_x1
        next_tile_id = tiles_ids[point_x2 + 1] if point_x2 + 1 < len(tiles_ids) else None

        while (
            next_tile_id in obj_tiles_ids
            and (point_x2 + 1) not in united_tiles_indexs
        ):
            point_x2 += 1
            try:
                next_tile_id = tiles_ids[point_x2]
            except IndexError:
                next_tile_id = 0

        united_tiles_indexs.extend(range(point_x1, point_x2 + 1))

        point_y = 0
        while all(
            (
                id_ in obj_tiles_ids and index not in united_tiles_indexs
                for index, id_ in enumerate(tiles_ids[point_x1 : point_x2 + 1])
            )
        ):
            point_y += 1
            point_x1 += point_y * cls.chunk_size
            point_x2 += point_y * cls.chunk_size
            if point_x1 >= len(tiles_ids):
                point_x1 = len(tiles_ids) - 1
            if point_x2 >= len(tiles_ids):
                point_x2 = len(tiles_ids) - 1
            united_tiles_indexs.extend(range(int(point_x1), int(point_x2) + 1))

        width = (point_x2 - point_x1 + 1) * cls.tile_size
        height = (point_y + 1) * cls.tile_size
        chunk_x = chunk.id % self.map_of_chunks_size
        chunk_y = chunk.id // self.map_of_chunks_size
        x = (
            (start_index % cls.chunk_size) * cls.tile_size
            + chunk_x * cls.chunk_size * cls.tile_size
        )
        y = (
            (start_index // cls.chunk_size) * cls.tile_size
            + chunk_y * cls.chunk_size * cls.tile_size
        )

        rect = pygame.Rect(x, y, width, height)
        type_name = tiles_info[str(tile_id)]
        arguments = copy.copy(register_objects_info[type_name])
        arguments.pop("Type", None)
        arguments.update(
            {
                "Name": f"{self.tilemap_name}{chunk.id}{start_index}",
                "Position": [x, y],
            }
        )

        game_object = copy.copy(cls.game_object_types[type_name])
        self._setup_game_object(game_object, arguments)

        chunk.rects_position.append([x, y])
        chunk.rects.append(rect)

        if isinstance(game_object, Wall):
            chunk.walls.add(game_object)
        else:
            chunk.game_objects.append(game_object)

    def _setup_game_object(self, game_object, arguments):
        """Применение аргументов к игровому объекту."""
        for attr_name, value in arguments.items():
            if hasattr(game_object, attr_name.lower()):
                setattr(game_object, attr_name.lower(), value)
        game_object.camera = self.camera
        game_object.scene = self.scene
        game_object.tilemap = self
        game_object.setup()

    def tick(self, *args):
        super().tick(*args)
        cls = type(self)

        # Определение текущего чанка игрока
        if self.scene.current_player_game_object:
            self.player_chunk_x = int(
                self.scene.current_player_game_object.position[0]
                // (cls.chunk_size * cls.tile_size)
            )
            self.player_chunk_y = int(
                self.scene.current_player_game_object.position[1]
                // (cls.chunk_size * cls.tile_size)
            )
        else:
            self.player_chunk_x = 0
            self.player_chunk_y = 0

        self.visible_chunks = utils.get_visible_chunks(
            self.player_chunk_x,
            self.player_chunk_y,
            self.scene.game.chunk_distance_fov,
            self.map_of_chunks_size,
            self.chunks,
        )

        for chunk in self.visible_chunks:
            chunk_x = (
                (chunk.id % self.map_of_chunks_size)
                * cls.chunk_size
                * cls.tile_size
            )
            chunk_y = (
                (chunk.id // self.map_of_chunks_size)
                * cls.chunk_size
                * cls.tile_size
            )
            self.screen.blit(
                chunk.image,
                (chunk_x + self.rect.x, chunk_y + self.rect.y),
            )

            if self.scene.game.is_developer_mode:
                pygame.draw.rect(
                    self.scene.game.screen,
                    "red",
                    (
                        chunk_x + self.rect.x,
                        chunk_y + self.rect.y,
                        cls.chunk_size * cls.tile_size,
                        chunk.size * cls.tile_size,
                    ),
                    1,
                )

        self.scene.game.draw_rects.append(self.rect)
        self.old_rect_position = [self.rect.x, self.rect.y]


class Input(GameObject):
    __slots__ = ["color", "radius", "border_radius", "default_position", "mouse_pressed", "touching_zone_box", "direction", "stick_position", "keys_data_base", "hot_keys_data_base", "modes", "mode", "hot_keys", "touching_zone_box_rect"]
    def __init__(self, *args):
        super().__init__(*args)
        self.color = None
        self.radius = 0
        self.border_radius = None
        self.default_position = None
        self.mouse_pressed = False
        self.touching_zone_box = None
        self.touching_zone_box_rect = None
        self.direction = [0, 0]
        self.stick_position = None
        self.keys_data_base = {
            "ESCAPE": pygame.K_ESCAPE,
            "W": pygame.K_w,
            "A": pygame.K_a,
            "S": pygame.K_s,
            "D": pygame.K_d
        }
        self.hot_keys_data_base = {
            "PLAYER_UP": None,
            "PLAYER_DOWN": None,
            "PLAYER_LEFT": None,
            "PLAYER_RIGHT": None
        }
        self.modes = {"Android":"Joystick","Windows":"Keyboard"}
        self.mode = "Joystick",
        self.hot_keys = {}
    def setup(self, *args):
        super().setup(*args)
        self.default_position = self.position
        self.stick_position = self.position
        self.rect.width = self.radius*2
        self.rect.height = self.radius*2
        for hot_key_name in self.hot_keys:
            self.hot_keys_data_base[hot_key_name] = self.keys_data_base[self.hot_keys[hot_key_name]]
        self.mode = self.modes[self.scene.game.ENVIRONMENT_OS]

    def tick(self, *args):
        super().tick(*args)

        if self.mode == "Joystick":
            mouse_position = self.scene.game.get_mouse_pos()
            if self.touching_zone_box_rect is None and self.touching_zone_box is not None:
                self.touching_zone_box_rect = pygame.Rect(self.touching_zone_box[0], self.touching_zone_box[1], self.touching_zone_box[2], self.touching_zone_box[3])
            try:
                if pygame.mouse.get_pressed()[0] and ((mouse_position[0] >= self.touching_zone_box[0] and mouse_position[0] <= self.touching_zone_box[0]+self.touching_zone_box[2] and mouse_position[1] >= self.touching_zone_box[1] and mouse_position[1] <= self.touching_zone_box[1]+self.touching_zone_box[3]) if not self.mouse_pressed else True):
                    pygame.draw.circle(self.scene.game.screen, self.color, [self.position[0], self.position[1]], self.radius, self.border_radius)
                    pygame.draw.circle(self.scene.game.screen, self.color, [self.stick_position[0], self.stick_position[1]], self.radius/2)
                    if not self.mouse_pressed:
                            self.position = [mouse_position[0], mouse_position[1]]
                            self.mouse_pressed = True
                    angle, vector_x, vector_y, lenght = utils.get_joystick_direction(self.position, mouse_position)
                    if lenght > self.radius:
                        lenght = self.radius
                    self.stick_position = [self.position[0]+vector_x*lenght, self.position[1]+vector_y*lenght]
                    self.direction = [vector_x, vector_y]
                    self.scene.game.draw_rects.append(self.rect)
                else:
                    self.position = self.default_position
                    self.stick_position = self.position
                    self.direction = [0, 0]
                    self.mouse_pressed = False
            except TypeError:
                pass
        elif self.mode == "Keyboard":
            keys = pygame.key.get_pressed()
            if keys[self.hot_keys_data_base["PLAYER_UP"]]:
                self.direction[1] = -1
            if keys[self.hot_keys_data_base["PLAYER_DOWN"]]:
                self.direction[1] = 1
            if keys[self.hot_keys_data_base["PLAYER_LEFT"]]:
                self.direction[0] = -1
            if keys[self.hot_keys_data_base["PLAYER_RIGHT"]]:
                self.direction[0] = 1
            if keys[self.hot_keys_data_base["PLAYER_UP"]] is False and keys[self.hot_keys_data_base["PLAYER_DOWN"]] is False:
                self.direction[1] = 0
            if keys[self.hot_keys_data_base["PLAYER_LEFT"]] is False and keys[self.hot_keys_data_base["PLAYER_RIGHT"]] is False:
                self.direction[0] = 0
class KeyBoard(GameObject):
    def __init__(self, *args):
        super().__init__(*args)
        self.direction = [0, 0]
        self.keys_data_base = {
            "ESCAPE": pygame.K_ESCAPE,
            "W": pygame.K_w,
            "A": pygame.K_a,
            "S": pygame.K_w,
            "D": pygame.K_w
        }
        self.hot_keys_data_base = {
            "PLAYER_UP": None,
            "PLAYER_DOWN": None,
            "PLAYER_LEFT": None,
            "PLAYER_RIGHT": None
        }
        self.hot_keys = {}
    def setup(self, *args):
        super().setup(*args)
        for hot_key_name in self.hot_keys:
            self.hot_keys_data_base[hot_key_name] = self.keys_data_base[self.hot_keys[hot_key_name]]
    def tick(self, *args):
        super().tick(*args)
        keys = pygame.key.get_pressed()
        if self.hot_keys_data_base["PLAYER_UP"]:
            if keys[self.hot_keys_data_base["PLAYER_UP"]]:
                self.direction[1] = 1

class Button(GameObject):
    __slots__ = ["width", "height", "text", "function", "color", "border_color", "border_radius", "change_scene_to_index", "font", "rendered_text", "rendered_text_size", "is_gui", "func_args", "func_name", "button_press_time"]
    def __init__(self, *args):
        super().__init__(*args)
        self.width = 0
        self.height = 0
        self.text = "Text"
        self.function = None
        self.color = None
        self.border_color = None
        self.border_radius = 0
        self.func_args = []
        self.font = None
        self.rendered_text = None
        self.rendered_text_size = None
        self.is_gui = True
        self.func_name = ""
        self.button_press_time = 1
    def setup(self, *args):
        super().setup(*args)
        self.function = getattr(self.scene.game, self.func_name)
        self.rect = pygame.Rect(self.position[0], self.position[1], self.width, self.height)
        self.font = pygame.font.SysFont("Ariel", self.width//(len(self.text)+1))
        self.rendered_text = self.font.render(self.text, True, self.border_color)
        self.rendered_text_size = self.rendered_text.get_size()

    def tick(self, *args):
        super().tick(*args)
        pygame.draw.rect(self.scene.game.screen, self.color, self.rect)
        pygame.draw.rect(self.scene.game.screen, self.border_color, self.rect, self.border_radius)
        position = utils.get_button_text_position(self.position, [self.width, self.height], self.rendered_text_size)
        self.scene.game.screen.blit(self.rendered_text, position)
        if self.ticks % self.button_press_time == 0:
            mouse_pos = self.scene.game.get_mouse_pos()
            if pygame.mouse.get_pressed()[0] and self.rect.collidepoint(mouse_pos):
                self.function(*self.func_args)
            self.scene.game.draw_rects.append(self.rect)


class Text(GameObject):
    __slots__ = ["text", "color", "font", "rendered_text", "rendered_text_size", "size", "mode", "last_time", "fps", "last_ticks"]
    def __init__(self, *args):
        super().__init__(*args)
        self.text = "Text"
        self.color = "black"
        self.font = None
        self.rendered_text = None
        self.rendered_text_size = [0, 0]
        self.size = 50
        self.mode = "Default"
        self.last_time = 0
        self.fps = 0
        self.last_ticks = self.ticks
    def setup(self, *args):
        super().setup(*args)
        self.font = pygame.font.SysFont("Ariel", self.size//len(self.text)*self.size)
        self.rendered_text = self.font.render(self.text, True, self.color)
        self.rendered_text_size = self.rendered_text.get_size()

    def tick(self, *args):
        if self.mode == "FpsCounter":
            current_time = time.time()
            if current_time - self.last_time >= 0:
                #self.fps = (self.ticks-self.last_ticks)//(current_time - self.last_time)
                self.fps = self.scene.game.clock.get_fps()
                self.last_time = current_time
                self.last_ticks = self.ticks
                if self.ticks % 60 == 0:
                    self.text = str(self.fps)
                    self.rendered_text = self.font.render(self.text, True, self.color)
                    self.rendered_text_size = self.rendered_text.get_size()
                    self.scene.game.draw_rects.append(self.rect)
        elif self.mode == "OnlineModeViewer":
            current_scene = self.scene.game.get_scene()
            if str(current_scene.is_online_mode) != self.text:
                self.rendered_text = self.font.render(self.text, True, self.color)
                self.rendered_text_size = self.rendered_text.get_size()
                self.scene.game.draw_rects.append(self.rect)
            self.text = str(self.scene.game.is_online_mode)
        self.scene.game.screen.blit(self.rendered_text, [self.position[0], self.position[1]])
        super().tick(*args)

class RoomLabel(GameObject):
    def __init__(self, *args):
        super().__init__(*args)
        self.position = [0, 0]
        self.is_gui = True
        self.buttons = []
        self.count_buttons = 0
        self.width = 0
        self.height = 0
        self.border_radius = 10
        self.old_position = self.position
        self.current_text_box = None
        self.text_box_name = None
        self.text_box_scene_name = None
        self.buttons_rects = []
        self.buttons_names = []
        self.buttons_func_args = []
        self.buttons_rendered_names = []
        self.font = None

    def update_room_label(self, rooms):
        count_buttons = len(rooms)
        self.buttons = []
        self.count_buttons = 0
        """
        for i in range(count_buttons):
            self.create_button(rooms[i], [rooms[i], self.current_text_box.text])
            self.count_buttons += 1
        """
        self.buttons_rects = []
        self.buttons_names = []
        self.buttons_func_args = []
        self.buttons_rendered_names = []
        for i in range(count_buttons):
            button_rect = pygame.Rect(self.position[0], self.position[1]+self.count_buttons*50, 300, 50)
            self.buttons_rects.append(button_rect)
            self.buttons_names.append(rooms[i])
            self.buttons_func_args.append(rooms[i])
            rendered_name = self.font.render(self.buttons_names[-1], False, "black")
            self.buttons_rendered_names.append(rendered_name)
            self.count_buttons += 1

    def create_button(self, text, func_args):
            button = Button()
            button.camera = self.camera
            button.scene = self.scene
            button.animation_name = "Camera"
            button.position = self.position
            button.width = 300
            button.height = 50
            button.position[1] = self.position[1] + self.count_buttons*button.height
            button.text = text
            button.color = "white"
            button.border_color = "black"
            button.border_radius = 5
            button.func_name = "join_room"
            button.func_args = func_args
            button.setup()
            self.buttons.append(button)
    def setup(self, *args):
        super().setup(*args)
        self.old_position = self.position
        if self.text_box_name is not None and self.text_box_scene_name is not None:
            scene = self.scene.game.scenes[self.text_box_scene_name]
            self.current_text_box = scene.game_objects[self.text_box_name]
        self.font = pygame.font.SysFont("Ariel", 50)

    def tick(self, *args):
        super().tick(*args)
        pygame.draw.rect(self.scene.game.screen, "black", [self.position[0],self.position[1], self.width, self.height], self.border_radius)
        for button in self.buttons:
            button.tick(*args)
        mouse_position = self.scene.game.get_mouse_pos()
        for i, button_rect in enumerate(self.buttons_rects):
            pygame.draw.rect(self.scene.game.screen, "white", button_rect)
            pygame.draw.rect(self.scene.game.screen, "black", button_rect, 5)
            button_rendered_name_size = self.buttons_rendered_names[i].get_size()
            self.scene.game.screen.blit(self.buttons_rendered_names[i], [button_rect.centerx-button_rendered_name_size[0]/2, button_rect.y])
            if pygame.mouse.get_pressed()[0] and button_rect.collidepoint(mouse_position):
                self.scene.game.join_room(self.buttons_func_args[i], self.current_text_box.text)
        self.position = self.old_position


class VisualKeyboard(GameObject):
    def __init__(self, scene, consumer):
        self.scene = scene
        self.consumer = consumer
        self.is_enabled = False
        self.width = 1366
        self.height = 300
        self.rect = pygame.Rect(0, 468, 1366, 300)
        self.symbols = "1234567890qwertyuiopasdfghjklzxcvbnm"
        self.buttons_rects = []
        self.buttons_position = [350, 468]
        self.row_lenght = 10
        self.button_size = 75
        self.font = pygame.font.SysFont("Ariel", 110)
        self.buttons_text_images = []
        self.text = ""
        self.ticks = 0
        self.space_button_position = [100, 700]
        self.backspace_button_position = [950, 700]
        self.space_button_rect = pygame.Rect(*self.space_button_position, 300, 75)
        self.backspace_button_rect = pygame.Rect(*self.backspace_button_position, 300, 75)
        self.space_button_text_image = self.font.render("space", False, "black")
        self.backspace_button_text_image = self.font.render("backspace", False, "black")
        for i, symbol in enumerate(self.symbols):
            x = self.buttons_position[0]+i%self.row_lenght*self.button_size
            y = self.buttons_position[1]+i//self.row_lenght*self.button_size
            button_rect = pygame.Rect(x, y, self.button_size, self.button_size)
            self.buttons_rects.append(button_rect)
            self.symbol_text_image = self.font.render(self.symbols[i], False, "black")
            self.buttons_text_images.append(self.symbol_text_image)
    def update(self, events):
        self.ticks += 1
    def draw(self, screen):
        screen_size = screen.get_size()
        self.width = screen_size[0]
        self.rect.width = self.width
        self.rect.height = self.height
        self.rect.y = screen_size[1]-self.rect.height
        self.buttons_position[1] = self.rect.y
        if self.is_enabled:
            pygame.draw.rect(screen, "white", self.rect)
            mouse_position = self.scene.game.get_mouse_pos()
            for i, button_rect in enumerate(self.buttons_rects):
                if pygame.mouse.get_pressed()[0]:
                    if button_rect.collidepoint(mouse_position):
                        pygame.draw.rect(screen, "grey", button_rect)
                        if self.ticks % 2 == 0:
                            self.text += self.symbols[i]
                            self.consumer(self.text)
                    else:
                        pygame.draw.rect(screen, "white", button_rect)
                x = self.buttons_position[0]+i%self.row_lenght*self.button_size
                y = self.buttons_position[1]+i//self.row_lenght*self.button_size
                screen.blit(self.buttons_text_images[i], [x, y])
            if pygame.mouse.get_pressed()[0]:
                if self.space_button_rect.collidepoint(mouse_position):
                    pygame.draw.rect(screen, "grey", self.space_button_rect)
                    if self.ticks % 2 == 0:
                        self.text += " "
                        self.consumer(self.text)
                else:
                    pygame.draw.rect(screen, "white", self.space_button_rect)
                if self.backspace_button_rect.collidepoint(mouse_position):
                    pygame.draw.rect(screen, "grey", self.backspace_button_rect)
                    if self.ticks % 2 == 0:
                        self.text = self.text[:len(self.text)-1]
                        self.consumer(self.text)
                else:
                    pygame.draw.rect(screen, "white", self.backspace_button_rect)
            screen.blit(self.space_button_text_image, self.space_button_position)
            screen.blit(self.backspace_button_text_image, self.backspace_button_position)
    def enable(self):
        self.is_enabled = True
    def disable(self):
        self.is_enabled = False

class TextBox(GameObject):
    __slots__ = ["text", "color", "font", "rendered_text", "rendered_text_size", "size", "mode", "last_time", "fps", "last_ticks", "visible_text", "text_color", "border_color", "border_radius", "space_signaling_time", "text_offset_y", "keyboard_is_visible", "max_count_symbols", "keyboard"]
    def __init__(self, *args):
        super().__init__(*args)
        self.text = "Text"
        self.visible_text = self.text
        self.color = "grey"
        self.text_color = "black"
        self.border_color = "black"
        self.border_radius = 1
        self.font = None
        self.rendered_text = None
        self.rendered_text_size = [0, 0]
        self.size = 50
        self.mode = "Default"
        self.last_time = 0
        self.fps = 0
        self.last_ticks = self.ticks
        self.width = None
        self.height = None
        self.space_signaling_time = None
        self.text_offset_y = 10
        self.keyboard_is_visible = False
        self.max_count_symbols = None
        self.keyboard = None
    def consumer(self, text):
        self.text = text
    def setup(self, *args):
        super().setup(*args)
        self.font = pygame.font.SysFont("Ariel", self.size//len(self.text)*self.size, bold=False, italic=True)
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        self.rendered_text_size = self.rendered_text.get_size()
        self.rect = pygame.Rect(self.position[0], self.position[1], self.width,self.height)
        self.keyboard = VisualKeyboard(self.scene, self.consumer)

    def tick(self, *args):
        if self.ticks % self.space_signaling_time == 0:
            symbol_index = self.visible_text.rfind("_")
            if symbol_index != -1:
                self.visible_text = self.text[:len(self.text)-1]
                if self.visible_text != self.text:
                    self.visible_text = self.text
            else:
                self.visible_text += "_"
            self.rendered_text = self.font.render(self.visible_text, True, self.text_color)
            self.rendered_text_size = self.rendered_text.get_size()

        pygame.draw.rect(self.scene.game.screen, self.color, self.rect)
        pygame.draw.rect(self.scene.game.screen, self.border_color, self.rect, self.border_radius)
        self.scene.game.screen.blit(self.rendered_text, [self.position[0], self.position[1]+self.text_offset_y])
        mouse_position = self.scene.game.get_mouse_pos()
        if pygame.mouse.get_pressed()[0]:
            if self.rect.collidepoint(mouse_position):
                if not self.keyboard_is_visible:
                    if self.ticks % 10 == 0:
                        if self.scene.game.compile_mode == "Apk":
                            pygame.key.start_text_input()
                        elif self.scene.game.compile_mode == "Pygbag":
                                self.keyboard.enable()
                        self.keyboard_is_visible = True
                else:
                    if self.ticks % 10 == 0:
                        if self.scene.game.compile_mode == "Apk":
                            pygame.key.stop_text_input()
                        elif self.scene.game.compile_mode == "Pygbag":
                            self.keyboard.disable()
                        self.keyboard_is_visible = False
            elif self.scene.game.get_scene() is not self.scene:
                    if self.scene.game.compile_mode == "Apk":
                        pygame.key.stop_text_input()
                    elif self.scene.game.compile_mode == "Pygbag":
                        self.keyboard.disable()
                    self.keyboard_is_visible = False
        super().tick(*args)

class Item(GameObject):
    def __init__(self):
        super().__init__()
        self.item_type = None

class Bullet(GameObject):
    def __init__(self):
        super().__init__()
        self.animation_name = "Bullet"

class Bariga(GameObject):
    def __init__(self):
        super().__init__()
        self.animation_name = "Bariga"
        self.required_item_type = None
        self.required_quantity = None
        self.given_item_type = None
        self.font = None
        self.rendered_text2 = None
        self.last_required_quantity = None
    def setup(self, *args):
        super().setup(*args)
        self.font = pygame.font.SysFont("Ariel", 40)
        self.rendered_text2 = self.font.render("0", True, "black")
    def tick(self, *args):
        super().tick(*args)
        if self.last_required_quantity != self.required_quantity:
            self.rendered_text2 = self.font.render(str(self.required_quantity), True, "black")
        self.last_required_quantity = self.required_quantity
        if self.scene.player_inventory is not None:
            self.scene.game.screen.blit(self.scene.player_inventory.hand_item_images[str(self.required_item_type)], [self.rect.x+15, self.rect.y+70])
        self.scene.game.screen.blit(self.rendered_text2, [self.rect.x+50, self.rect.y+70])
        if self.scene.player_inventory is not None:
            self.scene.game.screen.blit(self.scene.player_inventory.hand_item_images[str(self.given_item_type)], [self.rect.x+150, self.rect.y+70])

class Inventory(GameObject):
        def __init__(self, *args):
            super().__init__(*args)
            self.color = "black"
            self.position = [0, 0]
            self.is_gui = True
            self.box_size = 100
            self.box_image = None
            self.box_offset = 25
            self.box_count = 3
            self.box_rects = []
            self.choosed_box_index = 0
            self.player = None
            self.pick_up_box_rect = None
            self.throw_away_box_rect = None
            self.item_image_ids = {}
            self.item_images = {}
            self.hand_item_images = {}
            self.inventory_box_rect = None
            self.is_online_mode = False
        def setup(self, *args):
            super().setup(*args)
            self.box_image = pygame.Surface((self.box_size,self.box_size))
            self.box_image.fill(self.color)
            self.box_image.set_alpha(125)
            for i in range(self.box_count):
                rect = pygame.Rect(self.position[0]+i*self.box_size+i*self.box_offset, self.position[1], self.box_size, self.box_size)
                self.box_rects.append(rect)
            self.pick_up_box_rect = pygame.Rect(self.position[0]+self.box_count*self.box_size+self.box_count*self.box_offset, self.position[1], self.box_size, self.box_size//2)
            self.throw_away_box_rect = pygame.Rect(self.position[0]+self.box_count*self.box_size+self.box_count*self.box_offset, self.position[1]+self.box_size//2, self.box_size, self.box_size//2)
            self.inventory_box_rect = pygame.Rect(self.position[0], self.position[1], (self.box_count+1)*self.box_size+self.box_count*self.box_offset, self.box_size)
            for item_image_id in self.item_image_ids:
                path = "sprites"
                image = pygame.image.load(utils.path(path+"/"+self.item_image_ids[item_image_id]))
                item_image = pygame.transform.scale(image, (50,50))
                hand_item_image = image
                self.item_images.update({item_image_id:item_image})
                self.hand_item_images.update({item_image_id:hand_item_image})
        def tick(self, *args):
            super().tick(*args)
            mouse_position = self.scene.game.get_mouse_pos()
            mouse_is_pressed = pygame.mouse.get_pressed()[0]
            for i, rect in enumerate(self.box_rects):
                self.scene.game.screen.blit(self.box_image, [rect.x, rect.y])
                if self.player is not None:
                    self.scene.game.screen.blit(self.item_images[str(self.player.inventory_data[i])], [rect.x+self.box_size//4, rect.y+self.box_size//4])
                if mouse_is_pressed and rect.collidepoint(mouse_position):
                    self.choosed_box_index = i

            if self.player is not None:
                if self.player.hand_item_type != self.player.inventory_data[self.choosed_box_index]:
                        self.player.hand_item_type = self.player.inventory_data[self.choosed_box_index]
                        self.player.events.append(["Game object state changed", [7, self.player.id, self.player.velocity, self.player.position, self.player.type_id, self.player.nickname, self.player.inventory_data, self.player.hand_item_type, self.player.hp]])
            if self.player is None:
                player = Entity()
            else:
                player = self.player
            if mouse_is_pressed and self.pick_up_box_rect.collidepoint(mouse_position) and not player.hp <= 0:
                    min_distance = 100
                    min_distance_item = None
                    for item in self.scene.items:
                        distance = math.sqrt((item.position[0]-self.player.position[0])**2+(item.position[1]-self.player.position[1])**2)
                        if min_distance > distance:
                            min_distance = distance
                            min_distance_item = item
                    if min_distance_item is not None:
                        player_inventory_data = copy.copy(self.player.inventory_data)
                        player_inventory_data[self.choosed_box_index] = min_distance_item.item_type
                        self.player.events.append(["Game object state changed", [6, self.player.id, self.player.velocity, self.player.position, self.player.type_id, self.player.nickname, player_inventory_data, self.player.hand_item_type]])
            if mouse_is_pressed and self.throw_away_box_rect.collidepoint(mouse_position) and not player.hp <= 0:
                    player_inventory_data = copy.copy(self.player.inventory_data)
                    player_inventory_data[self.choosed_box_index] = 0
                    self.player.events.append(["Game object state changed", [6, self.player.id, self.player.velocity, self.player.position, self.player.type_id, self.player.nickname, player_inventory_data, self.player.hand_item_type]])

            pygame.draw.rect(self.scene.game.screen, "black", self.box_rects[self.choosed_box_index], 5)

            pygame.draw.rect(self.scene.game.screen, "green", self.pick_up_box_rect)

            pygame.draw.rect(self.scene.game.screen, "red", self.throw_away_box_rect)

class Hp(GameObject):
    def __init__(self, *args):
        super().__init__(*args)
        self.position = [0, 0]
        self.player = None
        self.width = 0
        self.height = 0
        self.visible_width = self.width
        self.max_player_hp = 10
        self.last_player_hp = self.max_player_hp
        self.color = "red"
        self.is_gui = True

    def setup(self, *args):
        super().setup(*args)
        self.rect = pygame.Rect(self.position[0], self.position[1], self.width, self.visible_width)

    def tick(self, *args):
        super().tick(*args)
        if self.player is not None:
            if self.player.hp != self.last_player_hp:
                self.visible_width = self.player.hp/self.max_player_hp*self.width
                self.rect = pygame.Rect(self.position[0], self.position[1], self.visible_width, self.height)
            self.last_player_hp = self.player.hp
        pygame.draw.rect(self.scene.game.screen, self.color, self.rect)

class Intro(GameObject):
    def __init__(self, *args):
        super().__init__(*args)
        self.position = [0, 0]
        self.color = "yellow"
        self.time = 600
        self.fps = 60
        self.alpha = 255
        self.screen_size = [1366, 768]

    def setup(self, *args):
        super().setup(*args)
        self.image = pygame.Surface(self.screen_size)
        self.image.fill(self.color)

    def tick(self, *args):
        super().tick(*args)
        self.image.set_alpha(0)
