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
        
        self.chunk_distance_fov = 1
        
        self.clock = None
        
        self.game_objects_render_distance = 0
        
    def setup(self, screen, virtual_screen_size, ENVIRONMENT_OS, TILE_SIZE, IP, CHUNK_DISTANCE_FOV, clock, GAME_OBJECTS_RENDER_DISTANCE):
        self.screen = screen
        self.virtual_screen_size = virtual_screen_size
        self.ENVIRONMENT_OS = ENVIRONMENT_OS
        self.TILE_SIZE = TILE_SIZE
        self.IP = IP
        self.chunk_distance_fov = CHUNK_DISTANCE_FOV
        self.clock = clock
        self.game_objects_render_distance = GAME_OBJECTS_RENDER_DISTANCE

    def tick(self, delta_time, changed_virtual_screen_position):
        scene = self.get_scene()
        
        scene.tick(delta_time, changed_virtual_screen_position)
        
        
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
          					
          					#print(event_name, event_data)
          					
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
        
        self.entities = {}
        
        self.walls = {}
        
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

    def setup(self):
        if self.player_controller_game_object_name:
        	self.player_controller_game_object = self.game_objects[self.player_controller_game_object_name[self.game.ENVIRONMENT_OS]]
        if self.current_camera_name:
        	self.current_camera = self.game_objects[self.current_camera_name]
        if self.tilemap_name:
        	self.tilemap = self.game_objects[self.tilemap_name]
        
    def add_game_object(self, new_game_object):
        if (new_game_object.is_only_for_smartphones is True and self.game.ENVIRONMENT_OS != "Windows"  and self.game.ENVIRONMENT_OS != "Linux") or new_game_object.is_only_for_smartphones is False:
         new_game_object.camera = self.current_camera
         self.game_objects.update({new_game_object.name:new_game_object})
         sorted_keys = sorted(self.game_objects)
         self.game_objects = {key:self.game_objects[key] for key in sorted_keys}
         if isinstance(new_game_object, Entity):
	         self.entities.update({new_game_object.name:new_game_object})
	         sorted_keys = sorted(self.entities)
	         self.entities = {key:self.entities[key] for key in sorted_keys}
        elif isinstance(new_game_object, Wall):
	         self.walls.update({new_game_object.name:new_game_object})
	         sorted_keys = sorted(self.walls)
	         self.walls = {key:self.walls[key] for key in sorted_keys}
        self.sprite_group.add(new_game_object)
    def remove_game_object(self, old_game_object):
        self.game_objects.pop(old_game_object.name)
        if isinstance(old_game_object, Entity):
        	self.entities.pop(old_game_object.name)
        elif isinstance(old_game_object, Wall):
        	self.walls.pop(old_game_object.name)
    
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
            						game_object.update(delta_time, changed_virtual_screen_position, self.game.screen, self.current_camera)
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
        self.is_gui = False
        self.animation_is_alpha = False
        
    def update(self, delta_time, changed_virtual_screen_position, screen, camera):
        self.screen = screen
        self.delta_time = delta_time
        self.changed_virtual_screen_position = changed_virtual_screen_position
        self.camera = camera
        
        self.screen.blit(self.image, self.rect)
        
        if not self.is_gui:
        	self.rect.x = self.position[0] - self.camera.position[0]
        	self.rect.y = self.position[1] - self.camera.position[1]
        else:
        	self.rect.x = self.position[0]
        	self.rect.y = self.position[1]

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
                try:
                	frame_path = sprites_folder_path+"/"+self.animation_name.lower()+"_"+animation_state.lower()+str(frame_number)+".png"
                	frame_image = pygame.image.load(utils.path(frame_path))
                except FileNotFoundError:
                	frame_path = sprites_folder_path+"/"+self.animation_name.lower()+"_"+animation_state.lower()+str(frame_number)+".jpg"
                	frame_image = pygame.image.load(utils.path(frame_path))

                frame_image = pygame.image.load(utils.path(frame_path))
                
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
    def __init__(self, *args):
    	super().__init__(*args)
    	self.speed = 0
    	self.velocity = [0, 0]
    	self.mode = "Default"
    	self.teleport_zone = [0, 450, 0, 450]
    	
    def update(self, *args):
    	super().update(*args)
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
    		
    def move(self, direction):
    	self.velocity[0] = direction[0]
    	self.velocity[1] = direction[1]
    		
    	self.position[0] += self.speed * self.velocity[0] * self.delta_time
    	self.rect.x = self.position[0] - self.camera.position[0]
    	
    	rects = []
    	for chunk in self.scene.tilemap.visible_chunks:
    		for rect in chunk.rects:
    			rects.append(rect)
    	
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
    	
    	rects = []
    	for chunk in self.scene.tilemap.visible_chunks:
    		for rect in chunk.rects:
    			rects.append(rect)
    			
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
    def update(self, *args):
        """
        mouse_pos = self.scene.game.get_mouse_pos()

        if self.rect.collidepoint(mouse_pos):
            self.position[0] = random.randint(0, 1316)
            self.position[1] = random.randint(0, 718)
        """
        super().update(*args)


class Camera(GameObject):
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
     
    def update(self, *args):
    	super().update(*args)
    	if self.mode == "Focus_at_game_object":
    		self.focus_at_game_object()
    	elif self.mode == "Static":
    		self.set_position(self.targeting_position)
    	elif self.mode == "Slow_focus_at_game_object":
    		self.slow_focus_at_game_object()

    		
    def focus_at_game_object(self):
    	if self.targeting_game_object:
    		self.set_position([self.targeting_game_object.position[0]-self.scene.game.virtual_screen_size[0]/2+self.targeting_game_object.rect.width/2, self.targeting_game_object.position[1]-self.scene.game.virtual_screen_size[1]/2+self.targeting_game_object.rect.height/2])
    
    def slow_focus_at_game_object(self):
    	if self.targeting_game_object:
    		self.set_position([self.position[0]+(self.targeting_game_object.rect.x-self.position[0])/self.slow_focus_time/self.FPS, self.position[1]+(self.targeting_game_object.rect.y-self.position[1])/self.slow_focus_time/self.FPS])

    def set_position(self, new_position):
        self.position = new_position

class Chunk:
	def __init__(self, id, image, size):
		self.size = size
		self.rects = []
		self.game_objects = []
		self.image = image
		self.id = id

class TileMap(GameObject):
    tiles_images = {}
    chunks_images = {}
    chunk_size = None
    tile_size = None

    def __init__(self, *args):
        self.tilemap_name = None
        self.tilemap_size = None
        self.map_of_chunks_size = None
        self.chunks = []
        self.visible_chunks = []
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
                try:
                	image = pygame.image.load(utils.path("sprites/"+tiles_info[tile_id]+".png"))
                	image.convert_alpha()
                except FileNotFoundError:
                	image = pygame.image.load(utils.path("sprites/"+tiles_info[tile_id]+".jpg"))
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
                tiles_ids += tilemap_info[chunk_x*cls.chunk_size+chunk_y*cls.chunk_size**2*self.map_of_chunks_size+self.tilemap_size*i:chunk_x*cls.chunk_size+chunk_y*cls.chunk_size**2*self.map_of_chunks_size+self.tilemap_size*i+cls.chunk_size]

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
                    
                    chunk.rects.append(game_object.rect)
                    
                    chunk.game_objects.append(game_object)
                else:
                    x = tile_index%cls.chunk_size*cls.tile_size
                    y = tile_index//cls.chunk_size*cls.tile_size
                    chunk_image.blit(cls.tiles_images[tile_id], [x, y])

    def update(self, *args):
        super().update(*args)
        cls = type(self)
        self.visible_chunks = []
        if self.scene.current_player_game_object:
            player_chunk_x = self.scene.current_player_game_object.position[0]//(cls.chunk_size*cls.tile_size)
            player_chunk_y = self.scene.current_player_game_object.position[1]//(cls.chunk_size*cls.tile_size)
        else:
        	player_chunk_x, player_chunk_y = 0, 0
        self.visible_chunks = self.chunks
        for chunk in self.visible_chunks:
	        chunk_x = chunk.id%self.map_of_chunks_size*cls.chunk_size*cls.tile_size
	        chunk_y = chunk.id//self.map_of_chunks_size*cls.chunk_size*cls.tile_size
	        self.screen.blit(chunk.image, [chunk_x+self.rect.x, chunk_y+self.rect.y])
        	for game_object in chunk.game_objects:
        		game_object.tick(delta_time, changed_virtual_screen_position, screen)

class JoyStick(GameObject):
	def __init__(self, *args):
		super().__init__(*args)
		self.color = None
		self.radius = None
		self.border_radius = None
		self.default_position = None
		self.mouse_pressed = False
		self.touching_zone_box = None
		self.direction = [0, 0]
		self.stick_position = None
	def setup(self, *args):
		super().setup(*args)
		self.default_position = self.position
		self.stick_position = self.position

	def update(self, *args):
		super().update(*args)
		pygame.draw.circle(self.scene.game.screen, self.color, [self.position[0], self.position[1]], self.radius, self.border_radius)
		pygame.draw.circle(self.scene.game.screen, self.color, [self.stick_position[0], self.stick_position[1]], self.radius/2)
		mouse_position = self.scene.game.get_mouse_pos()
		if pygame.mouse.get_pressed()[0] and ((mouse_position[0] >= self.touching_zone_box[0] and mouse_position[0] <= self.touching_zone_box[0]+self.touching_zone_box[2] and mouse_position[1] >= self.touching_zone_box[1] and mouse_position[1] <= self.touching_zone_box[1]+self.touching_zone_box[3]) if not self.mouse_pressed else True):
				if not self.mouse_pressed:
					self.position = [mouse_position[0], mouse_position[1]]
					self.mouse_pressed = True
				angle = math.atan2(mouse_position[1]-self.position[1], mouse_position[0]-self.position[0])
				vector_x = math.cos(angle)
				vector_y = math.sin(angle)
				lenght = math.sqrt((self.position[0]-mouse_position[0])**2+(self.position[1]-mouse_position[1])**2)
				if lenght > self.radius:
					lenght = self.radius
				self.stick_position = [self.position[0]+vector_x*lenght, self.position[1]+vector_y*lenght]
				self.direction = [vector_x, vector_y]
		else:
			self.position = self.default_position
			self.stick_position = self.position
			self.direction = [0, 0]
			self.mouse_pressed = False

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
	def update(self, *args):
		super().update(*args)
		keys = pygame.key.get_pressed()
		if self.hot_keys_data_base["PLAYER_UP"]:
		                  if keys[self.hot_keys_data_base["PLAYER_UP"]]:
		                  	self.direction[1] = 1
		
class Button(GameObject):
	def __init__(self, *args):
		super().__init__(*args)
		self.width = 0
		self.height = 0
		self.text = "Text"
		self.function = None
		self.color = None
		self.border_color = None
		self.border_radius = 0
		self.change_scene_to_index = None
		self.font = None
		self.rendered_text = None
		self.rendered_text_size = None
		self.is_gui = True
	def setup(self, *args):
		super().setup(*args)
		self.function = self.scene.game.change_current_scene
		self.rect = pygame.Rect(self.position[0], self.position[1], self.width, self.height)
		self.font = pygame.font.SysFont("Ariel", self.width//(len(self.text)+1))
		self.rendered_text = self.font.render(self.text, self.border_color, True)
		self.rendered_text_size = self.rendered_text.get_size()

	def update(self, *args):
		super().update(*args)
		pygame.draw.rect(self.scene.game.screen, self.color, self.rect)
		pygame.draw.rect(self.scene.game.screen, self.border_color, self.rect, self.border_radius)
		self.scene.game.screen.blit(self.rendered_text, [self.position[0]+self.width/2-self.rendered_text_size[0]/2, self.position[1]+self.height/2-self.rendered_text_size[1]/2])
		if self.ticks % 120 == 0:
			mouse_pos = self.scene.game.get_mouse_pos()
			if pygame.mouse.get_pressed()[0] and self.rect.collidepoint(mouse_pos):
				self.function(self.change_scene_to_index)

			
class Text(GameObject):
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

	def update(self, *args):
		self.scene.game.screen.blit(self.rendered_text, [self.position[0]+self.rendered_text_size[0]/2-self.rendered_text_size[0]/2, self.position[1]+self.rendered_text_size[1]/2-self.rendered_text_size[1]/2])
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
		elif self.mode == "OnlineModeViewer":
			if str(self.scene.game.is_online_mode) != self.text:
				self.rendered_text = self.font.render(self.text, self.color, True)
				self.rendered_text_size = self.rendered_text.get_size()
			self.text = str(self.scene.game.is_online_mode)
		super().update(*args)

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
			
	def update(self, *args):
		super().update(*args)
		self.image.set_alpha(0)
