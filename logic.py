import pygame
import copy
import math
import random
import time
import socket
import json
import utils


class Game:
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
        
        self.is_online_mode = False
        
        self.current_event = []
        
        self.ticks = 0
        
        self.itinerarium = None
        
        self.game_object_types = {}
        
        self.my_id = None
        
        self.network_checking_time = 20
        
        self.lagging_ticks = 15
        
        self.last_packet_time = time.time()
        
    def setup(self, screen, virtual_screen_size, ENVIRONMENT_OS, TILE_SIZE, IP):
        self.screen = screen
        self.virtual_screen_size = virtual_screen_size
        self.ENVIRONMENT_OS = ENVIRONMENT_OS
        self.TILE_SIZE = TILE_SIZE
        self.IP = IP
        
    def render(self):
        scene = self.get_scene()
        
        scene.draw()
        
    def tick(self, delta_time, changed_virtual_screen_position):
        self.current_event = []
        current_scene = self.get_scene()
        current_scene.tick(delta_time, changed_virtual_screen_position)
        if current_scene.is_online_mode:
        	self.is_online_mode = True
        else:
        	self.is_online_mode = False

        
        if self.is_online_mode:
          	if self.itinerarium is None:
          			try:
          				self.itinerarium = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          				self.itinerarium.setblocking(False)
          				self.current_event.append(["New client", [True]])
          				self.current_event.append(["Create room", ["Room"]])
          				self.current_event.append(["Join room", ["Room"]])          				
          			except ConnectionRefusedError:
          				self.current_scene.is_online_mode = False
          				self.is_online_mode = False
          				
          	if time.time() - self.last_packet_time > self.network_checking_time:
          				self.change_current_scene(0)
          				self.last_packet_time = time.time()
          				
          	if self.ticks % 120 == 0:
          		self.current_event.append(["Client alive", [True]])
          		
          	if self.current_event:
          			try:
	          			request = {"event_bus": self.current_event, "ticks": self.ticks}
	          			packet = json.dumps(request)
	          			data = packet.encode()
	          			self.itinerarium.sendto(data, tuple(self.IP))
	          		except BrokenPipeError:
	          			current_scene.is_online_mode = False
	          			self.is_online_mode = False
          			
          	try:
          			data = self.itinerarium.recv(1024)
          			packet = data.decode()
          			start_slace = packet.find("{")
          			end_slace = packet.find("}{")
          			if end_slace == -1:
          				end_slace = packet.rfind("}")
          			packet = packet[start_slace:end_slace+1]
          			if not packet:
          				packet = "{}"
          			else:
          				response = json.loads(packet)
          				
          				self.last_packet_time = time.time()
          				
          				if abs(self.ticks - response["ticks"]) > self.lagging_ticks:
          					self.current_event.append(["Get condition of the room", [True]])
          				
          				
          				for event in response["event_bus"]:
          					event_name = event[0]
          					event_data = event[1]
          					
          					print(event_name, event_data)
          					
          					if event_name == "Your ID":
          						self.my_id = event_data[0]
          					elif event_name == "Your player ID":
          						current_scene.my_player_id = event_data[0]
          					elif event_name == "Add game object":
          						if event_data[0] == "Player":
          							game_object = copy.copy(self.game_object_types["PeaShooter"])
          							game_object.name = "Z"+str(event_data[1])
          							game_object.id = event_data[1]
          							game_object.position = event_data[2]
          							game_object.scene = current_scene
          							game_object.camera = current_scene.current_camera
          							game_object.is_online_mode = True
          							game_object.setup()
          							current_scene.add_game_object(game_object)
          					elif event_name == "Your condition of the room":
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
        
    @property
    def scenes(self):
        return self.__scenes


class Scene:
    def __init__(self):        
        self.type = None
        
        self.name = None
        
        self.game_objects = {}
        
        self.game = None

        self.current_camera = None
        
        self.current_camera_name = None
        
        self.current_player_game_object = None
        
        self.player_game_object_name = None
        
        self.player_controller_game_object = None
        
        self.player_controller_game_object_name = None
        
        self.is_online_mode = False
        
        self.my_player_id = None

    def setup(self):
        if self.player_controller_game_object_name:
        	self.player_controller_game_object = self.game_objects[self.player_controller_game_object_name[self.game.ENVIRONMENT_OS]]
        if self.current_camera_name:
        	self.current_camera = self.game_objects[self.current_camera_name]
        
    def add_game_object(self, new_game_object):
        if (new_game_object.is_only_for_smartphones is True and self.game.ENVIRONMENT_OS != "Windows"  and self.game.ENVIRONMENT_OS != "Linux") or new_game_object.is_only_for_smartphones is False:
         new_game_object.camera = self.current_camera
         self.game_objects.update({new_game_object.name:new_game_object})
         sorted_keys = sorted(self.game_objects)
         self.game_objects = {key:self.game_objects[key] for key in sorted_keys}
    def remove_game_object(self, old_game_object):
        self.game_objects.pop(old_game_object.name)
    
    def draw(self):
        for game_object in self.game_objects.values():
            game_object.draw(self.game.screen)
    
    def tick(self, delta_time, changed_virtual_screen_position):
          		if self.my_player_id is not None:
          			if "Z"+str(self.my_player_id) in self.game_objects:
          				self.player_game_object_name = "Z"+str(self.my_player_id)
          		if self.player_game_object_name and self.current_player_game_object is None:
          			self.current_player_game_object = self.game_objects[self.player_game_object_name]
          			self.current_camera.targeting_game_object = self.current_player_game_object
          		if self.current_player_game_object is not None and self.player_controller_game_object.direction != [0, 0]:
          			self.current_player_game_object.move(self.player_controller_game_object.direction)
          		for game_object in self.game_objects.values():
          			if game_object.camera != self.current_camera:
          				game_object.camera = self.current_camera
          			game_object.update(delta_time, changed_virtual_screen_position)
          			self.game.current_event += game_object.events
          			game_object.events = []

class GameObject(pygame.sprite.Sprite):	
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

    def draw(self, screen):
        self.screen = screen
        
        screen.blit(self.image, self.rect)

    def update(self, delta_time, changed_virtual_screen_position):
        self.delta_time = delta_time
        self.changed_virtual_screen_position = changed_virtual_screen_position
        
        self.rect.x = self.position[0] - self.camera.position[0]
        self.rect.y = self.position[1] - self.camera.position[1]

        if self.ticks-self.last_frame_flip_ticks == self.animation_ticks[self.state][self.animation_current_frame]-1:
            if self.animation_current_frame + 1 > len(self.animation_frame_images[self.state]) - 1:
                self.animation_current_frame = 0
            else:
                self.animation_current_frame += 1

            self.last_frame_flip_ticks = self.ticks

        self.image = self.animation_frame_images[self.state][self.animation_current_frame]

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
                frame_path = sprites_folder_path+"/"+self.animation_name.lower()+"_"+animation_state.lower()+str(frame_number)+".png"

                frame_image = pygame.image.load(utils.path(frame_path))

                frame_image.convert_alpha()

                self.animation_frame_images[animation_state].append(frame_image)

        self.image = self.animation_frame_images[self.state][self.animation_current_frame]

        self.rect = self.image.get_rect(x=self.position[0]-self.camera.position[0], y=self.position[1]-self.camera.position[1])


class Entity(GameObject):
    def __init__(self, *args):
    	super().__init__(*args)
    	self.velocity = [0, 0]
    	
    def update(self, *args):
    	super().update(*args)
    	self.position[0] += self.velocity[0] * self.speed * self.delta_time
    	self.position[1] += self.velocity[1] * self.speed * self.delta_time
    def move(self, direction):
    	self.velocity[0] = direction[0]
    	self.velocity[1] = direction[1]
    		
    	self.position[0] += self.speed * self.velocity[0] * self.delta_time
    	self.rect.x = self.position[0] - self.camera.position[0]
    	
    	game_objects = [game_object for game_object in list(self.scene.game_objects.values())]
    	rects = [game_object.rect for game_object in game_objects]
    	rects.remove(self.rect)
    	collided_rect_index = self.rect.collidelist(rects)
    	try:
    		collided_rect = rects[collided_rect_index]
    	except IndexError:
    		pass
    		
    	if collided_rect_index != -1:
    		if self.velocity[0] > 0:
    			self.rect.right = collided_rect.left
    		elif self.velocity[0] < 0:
    			self.rect.left = collided_rect.right
    		self.position[0] = self.rect.x + self.camera.position[0]
    	
    	self.position[1] += self.speed * self.velocity[1] * self.delta_time
    	self.rect.y = self.position[1] - self.camera.position[1]
    	
    	game_objects = [game_object for game_object in list(self.scene.game_objects.values())]
    	rects = [game_object.rect for game_object in game_objects]
    	rects.remove(self.rect)
    	collided_rect_index = self.rect.collidelist(rects)
    	try:
    		collided_rect = rects[collided_rect_index]
    	except IndexError:
    		pass
    	
    	if collided_rect_index != -1:
    		if self.velocity[1] > 0:
    			self.rect.bottom = collided_rect.top
    		elif self.velocity[1] < 0:
    			self.rect.top = collided_rect.bottom
    		self.position[1] = self.rect.y + self.camera.position[1]
	
    	self.events.append(["Game object moved", [self.id, self.velocity]])
    	
    	self.velocity = [0, 0]


class Wall(GameObject):
    def update(self, delta_time, changed_virtual_screen_position):
        """
        mouse_pos = self.scene.game.get_mouse_pos()

        if self.rect.collidepoint(mouse_pos):
            self.position[0] = random.randint(0, 1316)
            self.position[1] = random.randint(0, 718)
        """
        super().update(delta_time, changed_virtual_screen_position)


class Camera(GameObject):
    def __init__(self, *args):
       super().__init__(*args)
       self.targeting_game_object = None
       self.mode = None
       self.target_game_object_name = None
       self.targeting_position = None
    def setup(self):
       super().setup()
       if self.target_game_object_name:
       	self.targeting_game_object = self.scene.game_objects[self.target_game_object_name]
       
    def draw(self, screen):
        pass
     
    def update(self, *args):
    	super().update(*args)
    	if self.mode == "Focus_at_game_object":
    		self.focus_at_game_object()
    	elif self.mode == "Static":
    		self.set_position(self.targeting_position)

    		
    def focus_at_game_object(self):
    	if self.targeting_game_object:
    		self.set_position([self.targeting_game_object.position[0]-self.scene.game.virtual_screen_size[0]/2+self.targeting_game_object.rect.width/2, self.targeting_game_object.position[1]-self.scene.game.virtual_screen_size[1]/2+self.targeting_game_object.rect.height/2])

    def set_position(self, new_position):
        self.position = new_position


class TileMap(GameObject):
    tiles_images = {}
    chunks_images = {}
    chunk_size = None
    tile_size = None

    def __init__(self, *args):
        self.tilemap_name = None
        self.tilemap_size = None
        self.map_of_chunks_size = None
        super().__init__(*args)

    def setup(self):
        super().setup()

        cls = type(self)

        tilemap_info = cls.config_tilemaps["TileMaps"][self.tilemap_name]

        tiles_info = cls.config_tiles["Tiles"]

        register_objects_info = cls.register_objects_info["Register_objects"]

        self.tilemap_size = int(math.sqrt(len(tilemap_info)))

        self.map_of_chunks_size = self.tilemap_size//cls.chunk_size

        for tile_id in tiles_info:
            if tiles_info[tile_id] not in cls.game_object_types:
                image = pygame.image.load(utils.path("sprites/"+tiles_info[tile_id]+".png"))
                cls.tiles_images.update({int(tile_id):image})

        for chunk_id in range(self.tilemap_size**2//cls.chunk_size):
            chunk_image = pygame.Surface((cls.chunk_size*cls.tile_size, cls.chunk_size*cls.tile_size))
            tiles_ids = []
            for i in range(cls.chunk_size):
                chunk_x = chunk_id%self.map_of_chunks_size
                chunk_y = chunk_id//self.map_of_chunks_size
                tiles_ids += (tilemap_info[chunk_x*cls.chunk_size+chunk_y*cls.chunk_size*self.tilemap_size+i*cls.chunk_size*self.tilemap_size:chunk_x*cls.chunk_size+chunk_y*cls.chunk_size*self.tilemap_size+i*cls.chunk_size*self.tilemap_size+cls.chunk_size])

            for tile_index, tile_id in enumerate(tiles_ids):
                if tile_id not in cls.tiles_images:
                    x = tile_index%cls.chunk_size*cls.tile_size+chunk_id%self.map_of_chunks_size*cls.chunk_size*cls.tile_size
                    y = tile_index//cls.chunk_size*cls.tile_size+chunk_id//self.map_of_chunks_size*cls.chunk_size*cls.tile_size

                    type_ = tiles_info[str(tile_id)]

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

                    self.scene.add_game_object(game_object)
                else:
                    x = tile_index%cls.chunk_size*cls.tile_size
                    y = tile_index//cls.chunk_size*cls.tile_size
                    chunk_image.blit(cls.tiles_images[tile_id], [x, y])
                    cls.chunks_images.update({chunk_id:chunk_image})

    def draw(self, screen):
        cls = type(self)
        for chunk_id in cls.chunks_images:
                chunk_image = cls.chunks_images[chunk_id]
                chunk_x = chunk_id%self.map_of_chunks_size*cls.chunk_size*cls.tile_size
                chunk_y = chunk_id//self.map_of_chunks_size*cls.chunk_size*cls.tile_size
                screen.blit(chunk_image, [chunk_x+self.rect.x, chunk_y+self.rect.y])

    def update(self, delta_
