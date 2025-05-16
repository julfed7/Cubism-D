# /// script
# dependencies = [
#  "pygame",
# ]
# ///

async def main():
	ENVIRONMENT_OS = "Android"
	
	PATH_TO_FOLDER_WHERE_SETTINGS = "settings"
	
	CONFIG_APP_FILE_NAME = "app.json"
	
	PATH_TO_FOLDER_WHERE_IMAGES = "sprites"
	
	PATH_TO_FOLDER_WHERE_SOUNDS = "sounds"
	
	ICON_FILE_NAME = "icon.png"
	
	CONFIG_ANIMATIONS_FILE_NAME = "register_animations.json"
	
	CONFIG_REGISTER_OBJECTS_FILE_NAME = "register_objects.json"
	
	CONFIG_SETUP_FILE_NAME = "setup.json"
	
	import utils
	
	config = utils.read_file(utils.path(PATH_TO_FOLDER_WHERE_SETTINGS+"/"+CONFIG_APP_FILE_NAME, ENVIRONMENT_OS))
	
	TITLE = config["App"]["Title"]
	
	FPS = config["App"]["FPS"]
	
	WIDTH = config["App"]["Width"]
	
	HEIGHT = config["App"]["Height"]
	
	CHUNK_SIZE = config["App"]["Chunk_size"]
	
	TILE_SIZE = config["App"]["Tile_size"]
	
	CHUNK_DISTANCE_FOV = config["App"]["Chunk_distance_fov"]
	
	GAME_OBJECTS_RENDER_DISTANCE = config["App"]["Game_objects_render_distance"]
	
	PLAYER_GAME_OBJECT_NAME = config["App"]["Player_game_object_name"]
	
	CAMERA_GAME_OBJECT_NAME = config["App"]["Camera_game_object_name"]
	
	IP = config["App"]["IP"]
	
	
	ticks = 0
	
	import time
	
	last_time = time.time()
	delta_time = last_time/1000
	
	last_screen_orientation = "Landscape"
	screen_orientation = "Landscape"
	
	is_running = 1
	
	changed_virtual_screen = None
	
	changed_virtual_screen_position = None
	
	import pygame
	
	pygame.init()
	
	screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN|pygame.DOUBLEBUF, 1)
	
	virtual_screen = pygame.Surface((WIDTH, HEIGHT))
	
	icon_image = pygame.image.load(utils.path("sprites/icon.png", ENVIRONMENT_OS))
	
	pygame.display.set_caption(TITLE)
	
	pygame.display.set_icon(icon_image)
	
	clock = pygame.time.Clock()
	
	import logic
	
	config_animations = utils.read_file(utils.path("settings/register_animations.json", ENVIRONMENT_OS))
	
	config_tilemaps = utils.read_file(utils.path("settings/register_tilemaps.json", ENVIRONMENT_OS))
	
	config_tiles = utils.read_file(utils.path("settings/register_tiles.json", ENVIRONMENT_OS))
	
	setattr(logic.GameObject, "config", config)
	setattr(logic.GameObject, "config_animations", config_animations)
	setattr(logic.TileMap, "config", config)
	setattr(logic.TileMap, "config_tilemaps", config_tilemaps)
	setattr(logic.TileMap, "config_tiles", config_tiles)
	setattr(logic.TileMap, "chunk_size", CHUNK_SIZE)
	setattr(logic.TileMap, "tile_size", TILE_SIZE)
	
	screen_size = screen.get_size()
	
	game = logic.Game()
	game.setup(virtual_screen, virtual_screen.get_size(), ENVIRONMENT_OS, TILE_SIZE, IP, CHUNK_DISTANCE_FOV, clock, GAME_OBJECTS_RENDER_DISTANCE)
	
	register_objects_info = utils.read_file(utils.path("settings/register_objects.json", ENVIRONMENT_OS))
	
	setup_info = utils.read_file(utils.path("settings/setup.json", ENVIRONMENT_OS))
	
	object_types = {
	  "Scene": logic.Scene,
	  "Entity": logic.Entity,
	  "Wall": logic.Wall,
	  "Camera": logic.Camera,
	  "TileMap": logic.TileMap,
	  "JoyStick": logic.JoyStick,
	  "KeyBoard": logic.KeyBoard,
	  "Button": logic.Button,
	  "Text": logic.Text,
	  "Intro": logic.Intro
	}
	
	game_object_types = {}
	
	for registered_object_name in register_objects_info["Register_objects"]:
		type_ = register_objects_info["Register_objects"][registered_object_name]["Type"]
		
		parameters = register_objects_info["Register_objects"][registered_object_name]
		
		game_object_type = object_types[type_]()
		
		for parameter_name in parameters:
	        	setattr(game_object_type, parameter_name.lower(), parameters[parameter_name])
		
		game_object_types.update({registered_object_name:game_object_type})
		
	setattr(logic.TileMap, "game_object_types", game_object_types)
	setattr(game, "game_object_types", game_object_types)
	setattr(logic.TileMap, "register_objects_info", register_objects_info)
	
	import copy
	
	registered_game_objects = []
	
	for registered_game_object_name in setup_info["Setup"]:
		type_ = setup_info["Setup"][registered_game_object_name]["Type"]
		
		arguments = setup_info["Setup"][registered_game_object_name]["Arguments"]
		
		arguments.update({"Name":registered_game_object_name})
		
		game_object = copy.copy(game_object_types[type_])
		
		for argument_name in arguments:
			if hasattr(game_object, argument_name.lower()):
				setattr(game_object, argument_name.lower(), arguments[argument_name])
			
		registered_game_objects.append(game_object)
	
	game_objects_to_scenes = {
	}
	
	for registered_game_object in registered_game_objects:
		if registered_game_object.type == "Scene":
			game_objects_to_scenes.update({registered_game_object:[]})
			
			for other_registered_game_object in registered_game_objects:
				if other_registered_game_object.name in registered_game_object.game_objects:
					game_objects_to_scenes[registered_game_object].append(other_registered_game_object)
		elif registered_game_object.name == CAMERA_GAME_OBJECT_NAME:
			for other_registered_game_object in registered_game_objects:
				if other_registered_game_object.name == PLAYER_GAME_OBJECT_NAME:
					registered_game_object.targeting_game_object = other_registered_game_object
			for other_registered_game_object in registered_game_objects:
				other_registered_game_object.camera = registered_game_object
	
			for other_registered_game_object in registered_game_objects:
				if other_registered_game_object.type == "Scene":
					other_registered_game_object.current_camera = registered_game_object
	for scene in game_objects_to_scenes:
		scene.game = game
		scene.game_objects = {}
	
		for game_object in game_objects_to_scenes[scene]:
			game_object.scene = scene
			game_object.setup()
	
			scene.add_game_object(game_object)
	
		scene.setup()
	
		game.add_scene(scene)
		
	pygame.event.set_allowed([pygame.QUIT, pygame.KEYUP])

	while is_running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				is_running = 0
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_ESCAPE:
					is_running = 0
		
		
	
		#Window
	
		last_screen_orientation = screen_orientation
	
		if screen_size[0] > screen_size[1]:
			screen_orientation = "Landscape"
		else:
			screen_orientation = "Portret"
			
		if ticks % 60 == 0:
			if screen_orientation == "Landscape":
				size = (screen_size[1]/HEIGHT*WIDTH, screen_size[1])
			elif screen_orientation == "Portret":
				size = (screen_size[0], screen_size[0]/WIDTH*HEIGHT)
				
			if screen_orientation != last_screen_orientation:
				screen.fill((0, 0, 0))
				
			screen_size = screen.get_size()
			
			changed_virtual_screen_position = (screen_size[0]/2-size[0]/2, screen_size[1]/2-size[1]/2)
	
		changed_virtual_screen = pygame.transform.scale(virtual_screen, size)
	
		game.changed_virtual_screen_position = changed_virtual_screen_position
	
		game.screen_size = screen_size
		
		
	
		screen.blit(changed_virtual_screen, changed_virtual_screen_position)
	
		#Draw
		virtual_screen.fill((255, 255, 255))
	
		#Moving game
		game.tick(delta_time, changed_virtual_screen_position)
		
		pygame.display.flip()
	
		#FPS
		ticks += 1
	
		delta_time = time.time()-last_time
	
		last_time = time.time()
		
		clock.tick(FPS)
		
		await asyncio.sleep(0)
	
	pygame.quit()

import asyncio

asyncio.run(main())