import pygame
import copy
import math
import random
import time
import socket
import json
import utils
import asyncio
import websockets
from websockets.sync.client import connect

class Game:
    __slots__ = ["__scenes", "current_scene", "screen", "changed_virtual_screen_position", "virtual_screen_size", "screen_size", "ENVIRONMENT_OS", "TILE_SIZE", "IP", "is_online_mode", "current_event", "ticks", "itinerarium", "game_object_types", "my_id", "network_checking_time", "lagging_ticks", "last_packet_time", "chunk_distance_fov", "clock", "game_objects_render_distance", "draw_rects", "SELF_PLAYER_TYPE_ID", "OTHER_PLAYER_TYPE_ID", "MAP_MAX_SIZE", "ONLINE_GAME_OBJECTS_RENDER_DISTANCE", "start_server"]
    def __init__(self):
        self.__scenes = {}
        
        self.current_scene = 0
        
        self.screen  = None
        
        self.changed_virtual_screen_position = None
        
        self.virtual_screen_size = None
        
        self.screen_size = None
        
        self.ENVIRONMENT_OS = None
        
        self.TILE_SIZE = None
        
        self.IP = None
        
        self.SELF_PLAYER_TYPE_ID = 0
        
        self.OTHER_PLAYER_TYPE_ID = 1
        
        self.MAP_MAX_SIZE = [-50000, 50000, -50000, 50000]
        
        self.ONLINE_GAME_OBJECTS_RENDER_DISTANCE = 300
        
        self.is_online_mode = False
        
        self.current_event = []
        
        self.ticks = 0
        
        self.itinerarium = None
        
        self.game_object_types = {}
        
        self.my_id = None
        
        self.network_checking_time = 5
        
        self.lagging_ticks = 2400
        
        self.last_packet_time = time.time()
        
        self.chunk_distance_fov = 1
        
        self.clock = None
        
        self.game_objects_render_distance = 0
        
        self.draw_rects = []
        
        self.start_server = None
        
    def setup(self, screen, virtual_screen_size, ENVIRONMENT_OS, TILE_SIZE, IP, CHUNK_DISTANCE_FOV, clock, GAME_OBJECTS_RENDER_DISTANCE):
        self.screen = screen
        self.virtual_screen_size = virtual_screen_size
        self.ENVIRONMENT_OS = ENVIRONMENT_OS
        self.TILE_SIZE = TILE_SIZE
        self.IP = IP
        self.chunk_distance_fov = CHUNK_DISTANCE_FOV
        self.clock = clock
        self.game_objects_render_distance = GAME_OBJECTS_RENDER_DISTANCE
        self.screen.fill((255,255,255))
 
    def tick(self, delta_time, changed_virtual_screen_position):
 
        self.draw_rects = []
        current_scene = self.get_scene()
        current_scene.tick(delta_time, changed_virtual_screen_position)
        if current_scene.is_online_mode:
        	self.is_online_mode = True
        else:
        	self.is_online_mode = False
     
        if self.itinerarium is None:
          	try:
          			self.itinerarium = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          			self.itinerarium.setblocking(False)
          			self.current_event.append(["New client", [True]])
          	except ConnectionRefusedError:
          				pass
          				
        if time.time() - self.last_packet_time > self.network_checking_time:
          	#self.change_current_scene(0)
          	self.current_event.append(["New client", [True]])
          	self.last_packet_time = time.time()
          				
        if self.ticks % 120 == 0:
          	self.current_event.append(["Client alive", [True]])
          	
        if self.ticks % 60 == 0 and current_scene.my_player_id is None and current_scene.is_online_mode is True:
        	self.current_event.append(["Get player ID", []])
        
        if current_scene.my_player_id is not None:
        	self.current_event.append(["Get game objects", []])
        
        if self.current_event != []:
              try:
              	request = {"event_bus": self.current_event, "ticks": self.ticks}
              	packet = json.dumps(request)
              	data = packet.encode()
              	self.itinerarium.sendto(data, tuple(self.IP))
              	self.current_event = []
              except BrokenPipeError:
              	pass
        try:
          	data = self.itinerarium.recv(65536)
          	packet = data.decode()
          	start_slace = packet.find("{")
          	end_slace = packet.find("}{")
          	if end_slace == -1:
          		end_slace = packet.rfind("}")
          	packet = packet[start_slace:end_slace+1]
          	if not packet:
          			packet = "{'event_bus':[], 'ticks':0}"
          			response = {"event_bus": [], "ticks":self.ticks}
          	else:
          			try:
          				response = json.loads(packet)
          			except json.decoder.JSONDecodeError:
          				response = {"event_bus": [], "ticks":self.ticks}
          	self.last_packet_time = time.time()
          	
          	if abs(self.ticks - response["ticks"]) > self.lagging_ticks:
          		pass
          		#self.current_event.append(["Get condition of the room", [True]])
          	
          	for event in response["event_bus"]:
          			event_name = event[0]
          			event_data = event[1]
          			if self.ticks % 60 == 0:
          				print(event_name, event_data)
          				
          			if event_name == "Your ID":
          				self.my_id = event_data[0]
          			elif event_name == "Your player ID":
          				current_scene.my_player_id = event_data[0]
          			elif event_name == "Add game object":
          				if event_data[0] == "Player":
          						game_object = copy.copy(self.game_object_types["PeaShooter"])
          				elif event_data[0] == "Cube":
          						game_object = copy.copy(self.game_object_types["Cube"])
          				game_object.name = "Z"+str(event_data[1])
          				game_object.id = event_data[1]
          				game_object.position = event_data[2]
          				game_object.scene = current_scene
          				game_object.camera = current_scene.current_camera
          				game_object.is_online_mode = True
          				game_object.setup()
          				current_scene.add_game_object(game_object)
          			elif event_name == "Your condition of the room":
          						self.ticks = response["ticks"]
          						live_game_objects_names = []
          						for game_object_data in event_data[0]["Game objects"]:
          								game_object_type = game_object_data[0]
          								game_object_name = "Z"+str(game_object_data[1])
          								game_object_id = game_object_data[1]
          								game_object_position = game_object_data[2]
          								live_game_objects_names.append(game_object_name)
          								if game_object_name not in current_scene.game_objects:
          									if game_object_type == "Player":
          										game_object = copy.copy(self.game_object_types["PeaShooter"])
          										game_object.name = game_object_name
          										game_object.id = game_object_id
          										game_object.position = game_object_position
          										game_object.scene = current_scene
          										game_object.camera = current_scene.current_camera
          										game_object.is_online_mode = True
          										game_object.setup()
          										current_scene.add_game_object(game_object)
          								else:
          									current_scene.game_objects[game_object_name].id = game_object_id
          									current_scene.game_objects[game_object_name].position = game_object_position
          								for game_object in list(current_scene.game_objects.values()):
          									if game_object.is_online_mode and game_object.name not in live_game_objects_names:
          										current_scene.remove_game_object(game_object)
          			elif event_name == "Game object moved":
          						current_scene.game_objects["Z"+str(event_data[0])].position = event_data[1]
          						print("Z"+str(event_data[0]))
          			elif event_name == "Your rooms":
          						room_label = current_scene.game_objects["JoinRoomRoomLabel"]
          						room_label.update_room_label(event_data[0])
          			elif event_name == "Game object state changed":
          				if event_data[0] == 2:
          					if event_data[4] == self.SELF_PLAYER_TYPE_ID:
          						current_scene.game_objects.pop(current_scene.current_player_game_object.name)
          						current_scene.current_player_game_object.name = "Z"+str(event_data[1])
          						current_scene.current_player_game_object.id = event_data[1]
          						current_scene.game_objects.update({current_scene.current_player_game_object.name:current_scene.current_player_game_object})
          					elif "Z"+str(event_data[1]) not in current_scene.game_objects:
          						game_object = copy.copy(self.game_object_types["PeaShooter"])
          						game_object.name = "Z"+str(event_data[1])
          						game_object.id = event_data[1]
          						game_object.position = event_data[2]
          						game_object.scene = current_scene
          						game_object.camera = current_scene.current_camera
          						game_object.is_online_mode = True
          						game_object.setup()
          						current_scene.game_objects.update({game_object.name:game_object})
          				current_scene.game_objects["Z"+str(event_data[1])].position = event_data[3]
          			elif event_name == "Add room":
          				room_label = self.scenes["JoinRoom"].game_objects["JoinRoomRoomLabel"]
          				room_label.update_room_label(event_data)
          			elif event_name == "Your game objects":
          				data = event_data[0]
          				current_scene.game_objects_data = data
          				if current_scene.my_player_id is not None:
          					try:
          						type_ = data[1][str(current_scene.my_player_id)][2]
          					except KeyError:
          						self.change_current_scene(0)
          					#type_ = "Player"
          				else:
          					type_ = None
          				if str(current_scene.my_player_id) in data[1] and "Z"+str(current_scene.my_player_id) not in current_scene.game_objects:
          						if type_ == "Player":
          							game_object = copy.copy(self.game_object_types["PeaShooter"])
          							game_object.nickname = data[1][str(current_scene.my_player_id)][3]
          							game_object.inventory = current_scene.player_inventory
          							current_scene.player_inventory.player = game_object
          							current_scene.player_hp.player = game_object
          						game_object.name = "Z"+str(current_scene.my_player_id)
          						game_object.id = current_scene.my_player_id
          						game_object.type_id = self.SELF_PLAYER_TYPE_ID
          						game_object.position = data[1][str(current_scene.my_player_id)][0]
          						game_object.velocity = data[1][str(current_scene.my_player_id)][1]
          						game_object.scene = current_scene
          						game_object.camera = current_scene.current_camera
          						game_object.is_online_mode = True
          						game_object.mode = "Player"
          						game_object.setup()
          						current_scene.add_game_object(game_object)
          				for game_object_id in data[0]:
          					if "Z"+str(game_object_id) not in current_scene.game_objects:
          						type_ = data[1][str(game_object_id)][2]
          						if type_ == "Player":
          							game_object = copy.copy(self.game_object_types["PeaShooter"])
          							game_object.mode = "Player"
          							game_object.nickname = data[1][str(game_object_id)][3]
          							game_object.inventory_data = data[1][str(game_object_id)][4]
          							game_object.hand_item_type = data[1][str(game_object_id)][5]
          							game_object.hp = data[1][str(game_object_id)][6]
          						elif type_ == "Zombie":
          							game_object = copy.copy(self.game_object_types["Zombie"])
          							game_object.mode = "Zombie"
          							game_object.nickname = data[1][str(game_object_id)][3]
          							game_object.inventory_data = data[1][str(game_object_id)][4]
          							game_object.hand_item_type = data[1][str(game_object_id)][5]
          							game_object.hp = data[1][str(game_object_id)][6]
          						elif type_ == "Item":
          							game_object = Item()
          							items_animations = {
          							  0: "Camera",
          							  1: "Pickaxe",
          							  2: "Sword",
          							  3: "Gun",
          							  4: "Coin"
          							}
          							try:
          								game_object.animation_name = items_animations[data[1][str(game_object_id)][3]]
          							except IndexError:
          								game_object.animation_name = "Camera"
          							game_object.item_type = data[1][str(game_object_id)][3]
          						elif type_ == "Tilemap":
          							TileMap.config_tilemaps["TileMaps"].update({f"Z_{game_object_id}":data[1][str(game_object_id)][3]})
          							
          							game_object = TileMap()
          							game_object.animation_name = "Camera"
          							game_object.tilemap_name = f"Z_{game_object_id}"
          						elif type_ == "Bullet":
          							game_object = Bullet()
          						elif type_ == "Bariga":
          							game_object = Bariga()
          							game_object.required_item_type = data[1][str(game_object_id)][3]
          							game_object.required_quantity = data[1][str(game_object_id)][4]
          							game_object.given_item_type = data[1][str(game_object_id)][5]
          						game_object.name = "Z"+str(game_object_id)
          						game_object.id = game_object_id
          						game_object.position = data[1][str(game_object_id)][0]
          						game_object.velocity = data[1][str(game_object_id)][1]
          						game_object.type_id = data[1][str(game_object_id)][2]
          						game_object.scene = current_scene
          						game_object.camera = current_scene.current_camera
          						game_object.is_online_mode = True
          						game_object.setup()
          						current_scene.add_game_object(game_object)
          					else:
          						current_scene.game_objects["Z"+str(game_object_id)].position = data[1][str(game_object_id)][0]
          						current_scene.game_objects["Z"+str(game_object_id)].velocity = data[1][str(game_object_id)][1]
          						type_ = data[1][str(game_object_id)][2]
          						if type_ == "Player":
          							current_scene.game_objects["Z"+str(game_object_id)].inventory_data = data[1][str(game_object_id)][4]
          							current_scene.game_objects["Z"+str(game_object_id)].hand_item_type = data[1][str(game_object_id)][5]
          							current_scene.game_objects["Z"+str(game_object_id)].hp = data[1][str(game_object_id)][6]
          						elif type_ == "Tilemap":
          							TileMap.config_tilemaps["TileMaps"][current_scene.game_objects["Z"+str(game_object_id)].tilemap_name] = data[1][str(game_object_id)][3]
          							for edited_chunk in data[1][str(game_object_id)][4]:
          								current_scene.game_objects["Z"+str(game_object_id)].edit_chunk(edited_chunk[0], edited_chunk[1])
          						elif type_ == "Bariga":
          							current_scene.game_objects["Z"+str(game_object_id)].required_item_type = data[1][str(game_object_id)][3]
          							current_scene.game_objects["Z"+str(game_object_id)].required_quantity = data[1][str(game_object_id)][4]
          							current_scene.game_objects["Z"+str(game_object_id)].given_item_type = data[1][str(game_object_id)][5]
          						"""
          						if game_object_id != current_scene.my_player_id:
          						"""
          			elif event_name == "Leave room now":
          				self.exit_from_room()
        except BlockingIOError and OSError:
          			pass
          			
        self.ticks += 1
        
    def get_scene(self):
        return list(self.scenes.values())[self.current_scene]
        
    def add_scene(self, new_scene):
        self.scenes.update({new_scene.name:new_scene})
        
    def remove_scene(self, scene_name):
        self.scenes.pop(scene_name)
    
    def get_mouse_pos(self):
        mouse_pos = list(pygame.mouse.get_pos())
        if self.screen_size[0] > self.screen_size[1]:
            virtual_screen_size = self.virtual_screen_size[0]
        else:
            virtual_screen = (self.virtual_screen_size[1], self.virtual_screen_size[0])
        mouse_pos[0] = (mouse_pos[0]-self.changed_virtual_screen_position[0])/(self.screen_size[0]-self.changed_virtual_screen_position[0]*2)*self.virtual_screen_size[0]
        mouse_pos[1] = (mouse_pos[1]-self.changed_virtual_screen_position[1])/(self.screen_size[1]-self.changed_virtual_screen_position[1]*2)*self.virtual_screen_size[1]
        return mouse_pos
        
    def change_current_scene(self, index):
        self.current_scene = index
        current_scene = self.get_scene()
        current_scene.ticks = 0
        #self.screen.fill((255,255,255))
    
    def join_room(self, room_name, nickname):
        self.current_event.append(["Join room", [room_name, nickname]])
        self.change_current_scene(6)
        
    def create_room(self):
        self.current_event.append(["Create room", [str(random.randint(1, 5))]])

        self.change_current_scene(0)
        
    def update_room_label(self, room_label_name):
        current_scene = self.get_scene()
        current_scene.room_label = current_scene.game_objects[room_label_name]
        self.current_event.append(["Get rooms", []])
    def exit_from_room(self):
        current_scene = self.get_scene()
        current_scene.my_player_id = None
        current_scene.player_game_object_name = None
        current_scene.current_player_game_object = None
        removing_game_objects = []
        
        for game_object_name in current_scene.game_objects:
         	game_object = current_scene.game_objects[game_object_name]
         	if game_object.is_online_mode:
         		removing_game_objects.append(game_object)
        for removing_game_object in removing_game_objects:
         	current_scene.remove_game_object(game_object)
         
        self.change_current_scene(0)
        self.current_event.append(["Leave room", []])
        
    @property
    def scenes(self):
        return self.__scenes


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
	            						if str(game_object.id) not in self.game_objects_data[1] and game_object.type_id is not None:
	            							removing_game_objects.append(game_object)
	            						game_object.tick(delta_time, changed_virtual_screen_position, self.game.screen, self.current_camera)
	            						self.game.current_event += game_object.events
	            						game_object.events = []
            except RuntimeError:
            	pass
            for removing_game_object in removing_game_objects:
            	self.remove_game_object(removing_game_object)
            self.ticks += 1

class GameObject(pygame.sprite.Sprite):
    __slots__ = ["type", "animation_name", "name", "position", "ticks", "last_frame_flip_ticks", "animation_ticks", "animation_current_frame", "state", "animation_frame_images", "image", "rect", "camera", "scene", "is_only_for_smartphones", "is_online_mode", "events", "id",  "is_gui", "animation_is_alpha", "not_animated", "is_rendered"]
    def __init__(self):
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
    def tick(self, delta_time, changed_virtual_screen_position, screen, camera):
        self.screen = screen
        self.delta_time = delta_time
        self.changed_virtual_screen_position = changed_virtual_screen_position
        self.camera = camera      
        
        if not self.is_rendered:
        	self.scene.game.draw_rects.append(self.rect)
        	self.is_rendered = True
        if self.position[0] > self.scene.game.MAP_MAX_SIZE[1]:
        	self.position[0] = self.scene.game.MAP_MAX_SIZE[1]
        elif self.position[0] < self.scene.game.MAP_MAX_SIZE[0]:
        	self.position[0] = self.scene.game.MAP_MAX_SIZE[0]
        if self.position[1] > self.scene.game.MAP_MAX_SIZE[1]:
        	self.position[1] = self.scene.game.MAP_MAX_SIZE[1]
        elif self.position[1] < self.scene.game.MAP_MAX_SIZE[0]:
        	self.position[1] = self.scene.game.MAP_MAX_SIZE[0]
        if not self.is_gui:
        	self.rect.x = self.position[0] - self.camera.position[0]
        	self.rect.y = self.position[1] - self.camera.position[1]
        else:
        	self.rect.x = self.position[0]
        	self.rect.y = self.position[1]
        
        if not self.not_animated:
	        if self.ticks-self.last_frame_flip_ticks == self.animation_ticks[self.state][self.animation_current_frame]-1:
	            if self.animation_current_frame + 1 > len(self.animation_frame_images[self.state]) - 1:
	                self.animation_current_frame = 0
	            else:
	                self.animation_current_frame += 1
	
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
            self.animation_ticks.update({animation_state:animation_info[animation_state]["Ticks"]})

            self.animation_frame_images.update({animation_state:[]})

            for frame_number in range(1, animation_info[animation_state]["Frames"]+1):
                try:
                	frame_path = sprites_folder_path+"/"+self.animation_name.lower()+"_"+animation_state.lower()+str(frame_number)+".png"
                	frame_image = pygame.image.load(utils.path(frame_path))
                except FileNotFoundError:
                	frame_path = sprites_folder_path+"/"+self.animation_name.lower()+"_"+animation_state.lower()+str(frame_number)+".jpg"
                	frame_image = pygame.image.load(utils.path(frame_path))
                if self.width is not None and self.height is not None:
                	frame_image = pygame.transform.scale(frame_image, (self.width, self.height))
                
                if self.animation_is_alpha:
                	frame_image.convert_alpha()
                else:
                	frame_image.convert()

                self.animation_frame_images[animation_state].append(frame_image)

        self.image = self.animation_frame_images[self.state][self.animation_current_frame]
        
        if not self.is_gui:
        	self.rect = self.image.get_rect(x=self.position[0]-self.camera.position[0], y=self.position[1]-self.camera.position[1])
        else:
        	self.rect = self.image.get_rect(x=self.position[0], y=self.position[1])


class Entity(GameObject):
    __slots__ = ["speed", "velocity", "mode", "teleport_zone"]
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
    	
    def setup(self, *args):
    	super().setup(*args)
    	self.font = pygame.font.SysFont("Ariel", 30)
    	self.rendered_text = self.font.render(self.nickname, True, "black")
    	
    def tick(self, *args):
    	if not self.hp <= 0:
    		super().tick(*args)
    	self.position[0] += self.velocity[0] * self.speed * self.delta_time
    	self.position[1] += self.velocity[1] * self.speed * self.delta_time
    	if self.mode == "Coin":
    		if self.ticks % 120 == 0:
	    		rects = [entity.rect for entity in self.scene.entities.values()]
	    		rects.remove(self.rect)
	    		collided_rect_index = self.rect.collidelist(rects)
	    		try:
	    			collided_rect = rects[collided_rect_index]
	    		except IndexError:
	    			pass
	    		if collided_rect_index != -1:
	    			self.position[0] = random.randint(self.teleport_zone[0], self.teleport_zone[1])
	    			self.position[1] = random.randint(self.teleport_zone[2], self.teleport_zone[3])
    	elif self.mode == "Player" and not self.hp <= 0:
	    	self.scene.game.screen.blit(self.rendered_text, [self.rect.x-len(self.nickname), self.rect.y-len(self.nickname)])
	    	if self.scene.player_inventory is not None:
	    		self.scene.game.screen.blit(self.scene.player_inventory.hand_item_images[str(self.hand_item_type)], [self.rect.right, self.rect.centery])
	    	if self.type_id == self.scene.game.SELF_PLAYER_TYPE_ID:
	    		mouse_is_pressed = pygame.mouse.get_pressed()[0]
	    		if mouse_is_pressed:
	    			mouse_position = self.scene.game.get_mouse_pos()
	    			offset_position = [mouse_position[0]-self.scene.game.virtual_screen_size[0]/2, mouse_position[1]-self.scene.game.virtual_screen_size[1]/2]
	    			touched_position = [self.position[0]+offset_position[0], self.position[1]+offset_position[1]]
	    			if self.hand_item_type != 0 and not self.scene.player_inventory.inventory_box_rect.collidepoint(mouse_position):
	    				if self.scene.game.ENVIRONMENT_OS == "Android":
	    					if not self.scene.player_controller_game_object.touching_zone_box_rect.collidepoint(mouse_position):
	    						self.events.append(["Item used", [touched_position]])
	    				else:
	    					self.events.append(["Item used", [touched_position]])
	    			
    	if self.is_moved and self.velocity != [0,0]:
	    	if self.type_id == self.scene.game.SELF_PLAYER_TYPE_ID:
	    		self.events.append(["Game object state changed", [2, self.id, [0,0], self.position, self.type_id, self.nickname, self.inventory_data, self.hand_item_type, self.hp]])
	    	self.is_moved = False
    
    def move(self, direction):
    	self.velocity[0] = direction[0]
    	self.velocity[1] = direction[1]

    	rects = []
    	if self.scene.tilemap is not None:
    		chunk = utils.get_here_chunk(self.scene.tilemap.player_chunk_x, self.scene.tilemap.player_chunk_y, self.scene.tilemap.chunks, self.scene.tilemap.map_of_chunks_size)
    		for i, rect in enumerate(chunk.rects):
    			rect.x = chunk.rects_position[i][0] - self.camera.position[0]
    			rect.y = chunk.rects_position[i][1] - self.camera.position[1]
    			rects.append(rect)   			
    	
    	self.position[0] += self.speed * self.velocity[0] * self.delta_time
    	self.rect.x = self.position[0] - self.camera.position[0]
    	
    	collided_rect_index = self.rect.collidelist(rects)
    	try:
    		collided_rect = rects[collided_rect_index]
    	except IndexError:
    		pass
    	print(rects)
    	if collided_rect_index != -1:
    			self.position[0] -= self.speed * self.velocity[0] * self.delta_time
    			self.rect.x = self.position[0] - self.camera.position[0]
	    	
    	self.position[1] += self.speed * self.velocity[1] * self.delta_time
    	self.rect.y = self.position[1] - self.camera.position[1]
    	
    	collided_rect_index = self.rect.collidelist(rects)
    	try:
    		collided_rect = rects[collided_rect_index]
    	except IndexError:
    			pass
    			
    	if collided_rect_index != -1:
    			self.position[1] -= self.speed * self.velocity[1] * self.delta_time
    			self.rect.y = self.position[1] - self.camera.position[1]
    	
    	if self.type_id == self.scene.game.SELF_PLAYER_TYPE_ID:
    		self.events.append(["Game object state changed", [2, self.id, self.velocity, self.position, self.type_id, self.nickname, self.inventory_data, self.hand_item_type, self.hp]])
    		
    	self.is_moved = True
    	
    	self.velocity = [0, 0]
    	
    	self.scene.game.draw_rects.append(self.rect)

class Wall(GameObject):
    def tick(self, *args):
        """
        mouse_pos = self.scene.game.get_mouse_pos()

        if self.rect.collidepoint(mouse_pos):
            self.position[0] = random.randint(0, 1316)
            self.position[1] = random.randint(0, 718)
        """
        super().tick(*args)
        self.scene.game.draw_rects.append(self.rect)
        
class Block(GameObject):
    def tick(self, *args):
        """
        mouse_pos = self.scene.game.get_mouse_pos()

        if self.rect.collidepoint(mouse_pos):
            self.position[0] = random.randint(0, 1316)
            self.position[1] = random.randint(0, 718)
        """
        super().tick(*args)
        self.scene.game.draw_rects.append(self.rect)


class Camera(GameObject):
    __slots__ = ["targeting_game_object", "mode", "target_game_object_name", "targeting_position", "focus_zone", "slow_focus_time", "FPS"]
    def __init__(self, *args):
       super().__init__(*args)
       self.targeting_game_object = None
       self.mode = None
       self.target_game_object_name = None
       self.targeting_position = None
       self.focus_zone = [0, 0, 0, 0]
       self.slow_focus_time = 0.5
       self.FPS = 60
    def setup(self):
       super().setup()
       if self.target_game_object_name:
       	self.targeting_game_object = self.scene.game_objects[self.target_game_object_name]
     
    def tick(self, *args):
    	super().tick(*args)
    	if self.mode == "Focus_at_game_object":
    		self.focus_at_game_object()
    	elif self.mode == "Static":
    		self.set_position(self.targeting_position)
    	elif self.mode == "Slow_focus_at_game_object":
    		self.slow_focus_at_game_object()

    		
    def focus_at_game_object(self):
    	if self.targeting_game_object:
    		position = utils.get_camera_position(self.targeting_game_object.position, self.targeting_game_object.rect, self.scene.game.virtual_screen_size)
    		self.set_position(position)
    
    def slow_focus_at_game_object(self):
    	if self.targeting_game_object:
    		self.set_position([self.position[0]+(self.targeting_game_object.rect.x-self.position[0])/self.slow_focus_time/self.FPS, self.position[1]+(self.targeting_game_object.rect.y-self.position[1])/self.slow_focus_time/self.FPS])

    def set_position(self, new_position):
        self.position = new_position

class Chunk:
	__slots__ = ["size", "rects", "rects_position", "rects_color", "game_objects", "walls", "image", "id", "tiles_ids"]
	def __init__(self, id, image, size):
		self.size = size
		self.rects = []
		self.rects_position = []
		self.rects_color = []
		self.game_objects = []
		self.walls = pygame.sprite.Group()
		self.image = image
		self.id = id
		self.tiles_ids = []

class TileMap(GameObject):
    __slots__ = ["tilemap_name", "tilemap_size", "map_of_chunks_size", "chunks", "visible_chunks", "old_rect_position", "player_chunk_x", "player_chunk_y"]
    tiles_images = {}
    chunks_images = {}
    chunk_size = None
    tile_size = None
    game_object_types = {}
    config_tilemaps = {}

    def __init__(self, *args):
        self.tilemap_name = None
        self.tilemap_size = None
        self.map_of_chunks_size = None
        self.chunks = []
        self.visible_chunks = []
        self.old_rect_position = [0,0]
        self.player_chunk_x = 0
        self.player_chunk_y = 0
        self.rects_optimization = False
        super().__init__(*args)
        
    def edit_chunk(self, chunk_id, tiles_ids):
            cls = type(self)
            chunk = self.chunks[chunk_id]
            for tile_index, tile_id in enumerate(tiles_ids):
                x = tile_index%cls.chunk_size*cls.tile_size
                y = tile_index//cls.chunk_size*cls.tile_size
                chunk.image.blit(cls.tiles_images[tile_id], [x, y])

    def setup(self):

        super().setup()
    	
        cls = type(self)

        tilemap_info = cls.config_tilemaps["TileMaps"][self.tilemap_name]

        tiles_info = cls.config_tiles["Tiles"]

        register_objects_info = cls.register_objects_info["Register_objects"]

        self.tilemap_size = int(math.sqrt(len(tilemap_info)))

        self.map_of_chunks_size = self.tilemap_size//cls.chunk_size
        
        objects_tiles_ids = []
        
        is_animated = True
        
        self.rect.width = self.map_of_chunks_size*cls.chunk_size*cls.tile_size
        self.rect.height = self.map_of_chunks_size*cls.chunk_size*cls.tile_size
        
        alpha_tiles_ids = []

        for tile_id in tiles_info:
            is_animated = True          
            if tiles_info[tile_id] in cls.game_object_types:
	            game_object = copy.copy(cls.game_object_types[tiles_info[tile_id]])
	            game_object.camera = self.camera
	            game_object.position = [0,0]
	            game_object.setup()
	            image = game_object.image
	            objects_tiles_ids.append(int(tile_id))
	            if not cls.game_object_types[tiles_info[tile_id]].not_animated:
	            	is_animated = False
            else:
                try:
                	image = pygame.image.load(utils.path("sprites/"+tiles_info[tile_id]+".png"))
                	image.convert_alpha()
                	alpha_tiles_ids.append(tile_id)
                except FileNotFoundError:
                	image = pygame.image.load(utils.path("sprites/"+tiles_info[tile_id]+".jpg"))
	            
            if is_animated:
                image.convert()
                cls.tiles_images.update({int(tile_id):image})

        for chunk_id in range(self.map_of_chunks_size**2):
            chunk_image = pygame.Surface((cls.chunk_size*cls.tile_size, cls.chunk_size*cls.tile_size))
            tiles_ids = []
            chunk = Chunk(chunk_id, chunk_image, cls.chunk_size)
            self.chunks.append(chunk)

            for i in range(cls.chunk_size):
                chunk_x = chunk_id%self.map_of_chunks_size
                chunk_y = chunk_id//self.map_of_chunks_size
                tiles_ids += tilemap_info[chunk_x*cls.chunk_size+chunk_y*(cls.chunk_size**2)*self.map_of_chunks_size+self.tilemap_size*i:chunk_x*cls.chunk_size+chunk_y*(cls.chunk_size**2)*self.map_of_chunks_size+self.tilemap_size*i+cls.chunk_size]
                
            chunk.tiles_ids = tiles_ids
            
            chunk_is_alpha = False
            
            for tile_id in tiles_ids:
                if tile_id in alpha_tiles_ids:
                	chunk_is_alpha = True
            if chunk_is_alpha:
                chunk_image.convert_alpha()
            else:
                chunk_image.convert()
                
            united_tiles_indexs = []
            for tile_index, tile_id in enumerate(tiles_ids):
                x = tile_index%cls.chunk_size*cls.tile_size
                y = tile_index//cls.chunk_size*cls.tile_size
                chunk_image.blit(cls.tiles_images[tile_id], [x, y])
                
                if not self.scene.is_online_mode and self.rects_optimization is True:
	                if tile_id in objects_tiles_ids and tile_index not in united_tiles_indexs:
	                	point_x1 = tile_index
	                	point_x2 = point_x1
	                	point_y = 0
	                	next_tile_id = tiles_ids[point_x2+1]
	                	while next_tile_id in objects_tiles_ids and point_x2+1 not in united_tiles_indexs:
	                		point_x2 += 1
	                		try:
	                			next_tile_id = tiles_ids[point_x2]
	                		except IndexError:
	                			next_tile_id = 0
	                	united_tiles_indexs += [index for index in range(point_x1, point_x2+1)]
	                	while False not in [True if id in objects_tiles_ids and index not in united_tiles_indexs else False for index, id in enumerate(tiles_ids[point_x1:point_x2+1])]:
	                	       point_y += 1
	                	       point_x1 += point_y*cls.chunk_size
	                	       point_x2 += point_y*cls.chunk_size
	                	       if point_x1 > len(tiles_ids)-1:
	                	       	point_x1 = len(tiles_ids)-1
	                	       if point_x2 > len(tiles_ids)-1:
	                	       	point_x2 = len(tiles_ids)-1
	                	       point_y = int(point_y)
	                	       point_x1 = int(point_x1)
	                	       point_x2 = int(point_x2)
	                	       united_tiles_indexs += [index for index in range(point_x1, point_x2+1)]

	                	width = (point_x2-point_x1+1)*cls.tile_size
	                	height = (point_y+1)*cls.tile_size
	                	x = tile_index%cls.chunk_size*cls.tile_size+chunk_id%self.map_of_chunks_size*cls.chunk_size*cls.tile_size
	                	y = tile_index//cls.chunk_size*cls.tile_size+chunk_id//self.map_of_chunks_size*cls.chunk_size*cls.tile_size
	                	rect = pygame.Rect(x, y, width, height)
	                	type_ = tiles_info[str(tile_id)]
	                	
	                	chunk.rects_position.append([x,y])
	                	chunk.rects.append(rect)
	                	
	                	arguments = copy.copy(register_objects_info[type_])
	                	arguments.pop("Type")
	                	arguments.update({"Name":self.tilemap_name+str(chunk_id)+str(tile_index)})
	                	arguments.update({"Position":[x, y]})
	                	game_object = copy.copy(cls.game_object_types[type_])
	                	for argument_name in arguments:
	                     	      		if hasattr(game_object, argument_name.lower()):
	                     	      			setattr(game_object, argument_name.lower(), arguments[argument_name])
	                	game_object.camera = self.camera
	                	game_object.scene = self.scene
	                	game_object.setup()
	                	if isinstance(game_object, Wall):
	                	    chunk.walls.add(game_object)
	                	else:
	                	    chunk.game_objects.append(game_object)
                else:
                	if tile_id in objects_tiles_ids:
                		width = cls.tile_size
                		height = cls.tile_size
                		x = tile_index%cls.chunk_size*cls.tile_size+chunk_id%self.map_of_chunks_size*cls.chunk_size*cls.tile_size
                		y = tile_index//cls.chunk_size*cls.tile_size+chunk_id//self.map_of_chunks_size*cls.chunk_size*cls.tile_size
                		rect = pygame.Rect(x, y, width, height)
                		type_ = tiles_info[str(tile_id)]
                		chunk.rects_position.append([x,y])
                		chunk.rects.append(rect)
                		arguments = copy.copy(register_objects_info[type_])
                		arguments.pop("Type")
                		arguments.update({"Name":self.tilemap_name+str(chunk_id)+str(tile_index)})
                		arguments.update({"Position":[x, y]})
                		game_object = copy.copy(cls.game_object_types[type_])
                		for argument_name in arguments:
                		    	      if hasattr(game_object, argument_name.lower()):
                		    	      	setattr(game_object, argument_name.lower(), arguments[argument_name])
                		game_object.camera = self.camera
                		game_object.scene = self.scene
                		game_object.setup()
                		if isinstance(game_object, Wall):
                			chunk.walls.add(game_object)
                		else:
                			chunk.game_objects.append(game_object)

    def tick(self, *args):
        super().tick(*args)
        cls = type(self)
        self.visible_chunks = []
        if self.scene.current_player_game_object:
        	self.player_chunk_x = int(self.scene.current_player_game_object.position[0]//(cls.chunk_size*cls.tile_size))
        	self.player_chunk_y = int(self.scene.current_player_game_object.position[1]//(cls.chunk_size*cls.tile_size))
        else:
        	self.player_chunk_x, self.player_chunk_y = 0, 0
        self.visible_chunks = utils.get_visible_chunks(self.player_chunk_x, self.player_chunk_y, self.scene.game.chunk_distance_fov, self.map_of_chunks_size, self.chunks)
        
        for chunk in self.visible_chunks:
         	chunk_x = chunk.id%self.map_of_chunks_size*cls.chunk_size*cls.tile_size
         	chunk_y = chunk.id//self.map_of_chunks_size*cls.chunk_size*cls.tile_size
         	self.screen.blit(chunk.image, [chunk_x+self.rect.x, chunk_y+self.rect.y])
         	
         	for i, game_object in enumerate(chunk.game_objects):
         		game_object.update(self.delta_time, self.changed_virtual_screen_position, self.screen, self.camera)
         
         	"""
         	for chunk in self.chunks:
         		for i, rect in enumerate(chunk.rects):
         			if len(chunk.rects) != len(chunk.rects_color):
         				rect_color = (random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))
         				chunk.rects_color.append(rect_color)
         			pygame.draw.rect(self.scene.game.screen, chunk.rects_color[i], rect)
         	"""

         	self.scene.game.draw_rects.append(self.rect)
        self.old_rect_position = [self.rect.x, self.rect.y]

class Input(GameObject):
	__slots__ = ["color", "raduis", "border_radius", "default_position", "mouse_pressed", "touching_zone_box", "direction", "stick_position", "keys_data_base", "hot_keys_data_base", "modes", "mode", "hot_keys"]
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
			if self.hot_keys_data_base["PLAYER_UP"]:
			                 	if keys[self.hot_keys_data_base["PLAYER_UP"]]:
			                 		self.direction[1] = -1
			                 	elif keys[self.hot_keys_data_base["PLAYER_DOWN"]]:
			                 		self.direction[1] = 1
			                 	elif keys[self.hot_keys_data_base["PLAYER_LEFT"]]:
			                 		self.direction[0] = -1
			                 	elif keys[self.hot_keys_data_base["PLAYER_RIGHT"]]:
			                 		self.direction[0] = 1
			                 	else:
			                 		self.direction = [0, 0]
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
	__slots__ = ["width", "height", "text", "function", "color", "border_color", "border_radius", "change_scene_to_index", "font", "rendered_text", "rendered_text_size", "is_gui"]
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
		self.rendered_text = self.font.render(self.text, self.border_color, True)
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
		self.rendered_text = self.font.render(self.text, self.color, True)
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
					self.rendered_text = self.font.render(self.text, self.color, True)
					self.rendered_text_size = self.rendered_text.get_size()
					self.scene.game.draw_rects.append(self.rect)
		elif self.mode == "OnlineModeViewer":
			current_scene = self.scene.game.get_scene()
			if str(current_scene.is_online_mode) != self.text:
				self.rendered_text = self.font.render(self.text, self.color, True)
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
			rendered_name = self.font.render(self.buttons_names[-1], "black", False)
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
		self.space_button_text_image = self.font.render("space", "black", False)
		self.backspace_button_text_image = self.font.render("backspace", "black", False)
		for i, symbol in enumerate(self.symbols):
			x = self.buttons_position[0]+i%self.row_lenght*self.button_size
			y = self.buttons_position[1]+i//self.row_lenght*self.button_size
			button_rect = pygame.Rect(x, y, self.button_size, self.button_size)
			self.buttons_rects.append(button_rect)
			self.symbol_text_image = self.font.render(self.symbols[i], "black", False)
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
	__slots__ = ["text", "color", "font", "rendered_text", "rendered_text_size", "size", "mode", "last_time", "fps", "last_ticks"]
	def __init__(self, *args):
		super().__init__(*args)
		self.text = "Text"
		self.visible_text = self.text
		self.color = "grey"
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
		self.font = pygame.font.SysFont("Ariel", self.size//len(self.text)*self.size)
		self.rendered_text = self.font.render(self.text, self.color, True)
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
			self.rendered_text = self.font.render(self.visible_text, self.color, True)
			self.rendered_text_size = self.rendered_text.get_size()
			
		pygame.draw.rect(self.scene.game.screen, self.color, self.rect)
		pygame.draw.rect(self.scene.game.screen, self.border_color, self.rect, self.border_radius)
		self.scene.game.screen.blit(self.rendered_text, [self.position[0], self.position[1]+self.text_offset_y])
		mouse_position = self.scene.game.get_mouse_pos()
		if pygame.mouse.get_pressed()[0]:
			if self.rect.collidepoint(mouse_position):
				if not self.keyboard_is_visible and self.scene.game.ENVIRONMENT_OS == "Android":
					#pygame.key.start_text_input()
					if self.ticks % 10 == 0:
						self.keyboard.enable()
						self.keyboard_is_visible = True
				else:
					#pygame.key.stop_text_input()
					if self.ticks % 10 == 0:
						self.keyboard.disable()
						self.keyboard_is_visible = False
			elif self.scene.game.get_scene() is not self.scene:
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
		self.rendered_text2 = self.font.render("0", "black", True)
	def tick(self, *args):
		super().tick(*args)
		if self.last_required_quantity != self.required_quantity:
			self.rendered_text2 = self.font.render(str(self.required_quantity), "black", True)
		self.last_required_quantity = self.required_quantity
		self.scene.game.screen.blit(self.scene.player_inventory.hand_item_images[str(self.required_item_type)], [self.rect.x+15, self.rect.y+70])
		self.scene.game.screen.blit(self.rendered_text2, [self.rect.x+50, self.rect.y+70])
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
				item_image = pygame.image.load(path+"/"+self.item_image_ids[item_image_id])
				hand_item_image = pygame.transform.scale(item_image, (25,25))
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
					
			if mouse_is_pressed and self.pick_up_box_rect.collidepoint(mouse_position) and not self.player.hp <= 0:
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
			if mouse_is_pressed and self.throw_away_box_rect.collidepoint(mouse_position) and not self.player.hp <= 0:
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
