import asyncio
import copy
import sys
import time
from io import StringIO

import pygame

import logic
import utils


# ============================== КОНФИГУРАЦИЯ ==============================
class Config:
    DEVICE_TYPE = "smartphone"          # "smartphone" или "computer"
    COMPILE_MODE = "Apk"                # "Apk" или "Exe"

    PATH_SETTINGS = "settings"
    PATH_IMAGES = "sprites"
    PATH_SOUNDS = "sounds"

    FILE_APP_CONFIG = "app.json"
    FILE_ANIMATIONS = "register_animations.json"
    FILE_TILEMAPS = "register_tilemaps.json"
    FILE_TILES = "register_tiles.json"
    FILE_OBJECTS = "register_objects.json"
    FILE_SETUP = "setup.json"
    FILE_ICON = "icon.png"

    PLAYER_OBJECT_NAME = None
    CAMERA_OBJECT_NAME = None
    TEXT_BOX_SCENE_NAME = None
    TEXT_BOX_NAME = None


# ============================== ГЛАВНЫЙ КЛАСС ==============================
class GameApplication:
    def __init__(self):
        self.environment_os = None
        self.screen = None
        self.virtual_screen = None
        self.clock = None
        self.game = None
        self.text_box = None

        self.ticks = 0
        self.last_time = 0.0
        self.delta_time = 0.0

        self.screen_size = (0, 0)
        self.last_screen_orientation = "Landscape"
        self.screen_orientation = "Landscape"

        self.changed_virtual_screen = None
        self.changed_virtual_screen_position = None

        self.stdout_buffer = StringIO()
        self.old_stdout = sys.stdout

        self.config = None
        self.config_animations = None
        self.config_tilemaps = None
        self.config_tiles = None
        self.register_objects_info = None
        self.setup_info = None

        self.width = 0
        self.height = 0
        self.fps = 0
        self.chunk_size = 0
        self.tile_size = 0
        self.chunk_distance_fov = 0
        self.render_distance = 0
        self.ip = ""

    # ----------------------------------------------------------------------
    def _setup_environment(self):
        if Config.DEVICE_TYPE == "smartphone":
            self.environment_os = "Android"
        elif Config.DEVICE_TYPE == "computer":
            self.environment_os = "Windows"

        sys.stdout = utils.Tee(sys.stdout, self.stdout_buffer)

        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        self.virtual_screen = pygame.Surface((self.width, self.height))
        self.clock = pygame.time.Clock()

        icon = pygame.image.load(utils.path(f"{Config.PATH_IMAGES}/{Config.FILE_ICON}", self.environment_os))
        pygame.display.set_icon(icon)
        pygame.display.set_caption(self.config["App"]["Title"])
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYUP])

    # ----------------------------------------------------------------------
    def _load_configs(self):
        app_path = utils.path(f"{Config.PATH_SETTINGS}/{Config.FILE_APP_CONFIG}", self.environment_os)
        self.config = utils.read_file(app_path)

        self.width = self.config["App"]["Width"]
        self.height = self.config["App"]["Height"]
        self.fps = self.config["App"]["FPS"]
        self.chunk_size = self.config["App"]["Chunk_size"]
        self.tile_size = self.config["App"]["Tile_size"]
        self.chunk_distance_fov = self.config["App"]["Chunk_distance_fov"]
        self.render_distance = self.config["App"]["Game_objects_render_distance"]
        self.ip = self.config["App"]["IP"]

        Config.PLAYER_OBJECT_NAME = self.config["App"]["Player_game_object_name"]
        Config.CAMERA_OBJECT_NAME = self.config["App"]["Camera_game_object_name"]
        Config.TEXT_BOX_SCENE_NAME = self.config["App"]["Text_box_scene_name"]
        Config.TEXT_BOX_NAME = self.config["App"]["Text_box_name"]

        anim_path = utils.path(f"{Config.PATH_SETTINGS}/{Config.FILE_ANIMATIONS}", self.environment_os)
        self.config_animations = utils.read_file(anim_path)

        tilemap_path = utils.path(f"{Config.PATH_SETTINGS}/{Config.FILE_TILEMAPS}", self.environment_os)
        self.config_tilemaps = utils.read_file(tilemap_path)

        tiles_path = utils.path(f"{Config.PATH_SETTINGS}/{Config.FILE_TILES}", self.environment_os)
        self.config_tiles = utils.read_file(tiles_path)

        objects_path = utils.path(f"{Config.PATH_SETTINGS}/{Config.FILE_OBJECTS}", self.environment_os)
        self.register_objects_info = utils.read_file(objects_path)

        setup_path = utils.path(f"{Config.PATH_SETTINGS}/{Config.FILE_SETUP}", self.environment_os)
        self.setup_info = utils.read_file(setup_path)

    # ----------------------------------------------------------------------
    def _inject_configs_into_logic(self):
        setattr(logic.GameObject, "config", self.config)
        setattr(logic.GameObject, "config_animations", self.config_animations)
        setattr(logic.TileMap, "config", self.config)
        setattr(logic.TileMap, "config_tilemaps", self.config_tilemaps)
        setattr(logic.TileMap, "config_tiles", self.config_tiles)
        setattr(logic.TileMap, "chunk_size", self.chunk_size)
        setattr(logic.TileMap, "tile_size", self.tile_size)

    # ----------------------------------------------------------------------
    def _create_game_object_types(self):
        object_types = {
            "Scene": logic.Scene,
            "Entity": logic.Entity,
            "Wall": logic.Wall,
            "Camera": logic.Camera,
            "TileMap": logic.TileMap,
            "Input": logic.Input,
            "KeyBoard": logic.Input,
            "JoyStick": logic.Input,
            "Button": logic.Button,
            "Text": logic.Text,
            "Intro": logic.Intro,
            "RoomLabel": logic.RoomLabel,
            "TextBox": logic.TextBox,
            "Inventory": logic.Inventory,
            "Hp": logic.Hp,
            "Block": logic.Block,
        }

        game_object_types = {}
        for obj_name, obj_data in self.register_objects_info["Register_objects"].items():
            obj_type = object_types[obj_data["Type"]]()
            for param, value in obj_data.items():
                setattr(obj_type, param.lower(), value)
            game_object_types[obj_name] = obj_type

        setattr(logic.TileMap, "game_object_types", game_object_types)
        setattr(self.game, "game_object_types", game_object_types)
        setattr(logic.TileMap, "register_objects_info", self.register_objects_info)

        return game_object_types

    # ----------------------------------------------------------------------
    def _instantiate_game_objects(self, game_object_types):
        registered_objects = []
        for obj_name, obj_data in self.setup_info["Setup"].items():
            obj_type = obj_data["Type"]
            arguments = obj_data["Arguments"].copy()
            arguments["Name"] = obj_name

            game_obj = copy.copy(game_object_types[obj_type])
            # Устанавливаем все аргументы без проверки hasattr
            for arg_name, arg_value in arguments.items():
                setattr(game_obj, arg_name.lower(), arg_value)
            registered_objects.append(game_obj)
        return registered_objects

    # ----------------------------------------------------------------------
    def _bind_objects_to_scenes(self, registered_objects):
        # Группируем объекты по сценам
        scenes = {}
        for obj in registered_objects:
            if obj.type == "Scene":
                scenes[obj] = []

        for scene in scenes:
            for obj in registered_objects:
                if hasattr(obj, 'name') and obj.name in scene.game_objects:
                    scenes[scene].append(obj)

        # Поиск камеры и игрока
        camera = None
        player = None
        for obj in registered_objects:
            if obj.name == Config.CAMERA_OBJECT_NAME:
                camera = obj
            elif obj.name == Config.PLAYER_OBJECT_NAME:
                player = obj

        # Авто-создание камеры при отсутствии
        if camera is None:
            print(f"ВНИМАНИЕ: Камера '{Config.CAMERA_OBJECT_NAME}' не найдена. Создаю стандартную.")
            camera = logic.Camera()
            camera.name = Config.CAMERA_OBJECT_NAME
            camera.type = "Camera"
            camera.position = [0, 0]
            registered_objects.append(camera)
            if scenes:
                first_scene = list(scenes.keys())[0]
                scenes[first_scene].append(camera)
            else:
                default_scene = logic.Scene()
                default_scene.name = "DefaultScene"
                default_scene.type = "Scene"
                default_scene.game_objects = []
                registered_objects.append(default_scene)
                scenes[default_scene] = [camera]

        if camera and player:
            camera.targeting_game_object = player

        for obj in registered_objects:
            obj.camera = camera
            if obj.type == "Scene":
                obj.current_camera = camera

        # Добавление объектов в сцены и вызов setup
        for scene, objects in scenes.items():
            scene.game = self.game
            scene.game_objects = {}
            for obj in objects:
                obj.scene = scene
                obj.setup()
                scene.add_game_object(obj)
            scene.setup()
            self.game.add_scene(scene)

    # ----------------------------------------------------------------------
    def _init_game(self):
        self.game = logic.Game()
        self.game.setup(
            self.virtual_screen,
            self.virtual_screen.get_size(),
            self.environment_os,
            self.tile_size,
            self.ip,
            self.chunk_distance_fov,
            self.clock,
            self.render_distance,
            Config.COMPILE_MODE,
        )

    # ----------------------------------------------------------------------
    def _get_text_box(self):
        if Config.TEXT_BOX_SCENE_NAME and Config.TEXT_BOX_NAME:
            scene = self.game.scenes.get(Config.TEXT_BOX_SCENE_NAME)
            if scene:
                return scene.game_objects.get(Config.TEXT_BOX_NAME)
        return None

    # ----------------------------------------------------------------------
    def _handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_BACKSPACE and self.text_box:
                    self.text_box.text = self.text_box.text[:-1]
                elif (
                    self.text_box
                    and (Config.COMPILE_MODE in ("Exe", "Apk"))
                    and len(self.text_box.text) + 1 <= self.text_box.max_count_symbols
                ):
                    self.text_box.text += event.unicode
        return True

    # ----------------------------------------------------------------------
    def _update_screen_transform(self):
        self.screen_size = self.screen.get_size()
        self.last_screen_orientation = self.screen_orientation
        self.screen_orientation = "Landscape" if self.screen_size[0] > self.screen_size[1] else "Portret"

        if self.screen_orientation == "Landscape":
            new_size = (self.screen_size[1] / self.height * self.width, self.screen_size[1])
        else:
            new_size = (self.screen_size[0], self.screen_size[0] / self.width * self.height)

        if self.screen_orientation != self.last_screen_orientation:
            self.screen.fill((0, 0, 0))

        self.changed_virtual_screen_position = (
            self.screen_size[0] / 2 - new_size[0] / 2,
            self.screen_size[1] / 2 - new_size[1] / 2,
        )
        self.changed_virtual_screen = pygame.transform.scale(self.virtual_screen, new_size)

    # ----------------------------------------------------------------------
    def _draw(self):
        self.screen.blit(self.changed_virtual_screen, self.changed_virtual_screen_position)
        self.virtual_screen.fill((255, 255, 255))

        # !!! Важно: передаём в game актуальные размеры экрана и позицию !!!
        self.game.screen_size = self.screen_size
        self.game.changed_virtual_screen_position = self.changed_virtual_screen_position

        self.game.tick(self.delta_time, self.changed_virtual_screen_position)

        if self.text_box:
            events = pygame.event.get()
            self.text_box.keyboard.update(events)
            self.text_box.keyboard.draw(self.virtual_screen)

        pygame.display.flip()

    # ----------------------------------------------------------------------
    async def run(self):
        self._load_configs()
        self._setup_environment()
        self._init_game()
        self._inject_configs_into_logic()

        game_object_types = self._create_game_object_types()
        registered_objects = self._instantiate_game_objects(game_object_types)
        self._bind_objects_to_scenes(registered_objects)

        self.text_box = self._get_text_box()

        self.last_time = time.time()
        running = True

        while running:
            events = pygame.event.get()
            running = self._handle_events(events)

            self._update_screen_transform()
            self._draw()

            self.ticks += 1
            now = time.time()
            self.delta_time = now - self.last_time
            self.last_time = now
            
            self.game.delta_time = self.delta_time

            self.clock.tick(self.fps)
            await asyncio.sleep(0)

        sys.stdout = self.old_stdout
        with open("output.txt", "w") as f:
            f.write(self.stdout_buffer.getvalue())
        pygame.quit()


# ============================== ТОЧКА ВХОДА ==============================
async def main():
    app = GameApplication()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())