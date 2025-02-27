import utils
import pygame
import copy
import math
import random


class Game:
    def __init__(self):
        self.__scenes = {}
        
        self.__current_scene = 0
        
        self.screen  = None
        
        self.changed_virtual_screen_position = None
        
        self.virtual_screen_size = None
        
        self.screen_size = None
        
    def setup(self, screen, virtual_screen_size):
        self.screen = screen
        self.virtual_screen_size = virtual_screen_size
        
    def render(self):
        scene = self.get_scene()
        
        scene.draw()
        
    def tick(self, delta_time, changed_virtual_screen_position):
        self.get_scene().tick(delta_time, changed_virtual_screen_position)
        
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
        
    @property
    def scenes(self):
        return self.__scenes
        
    @property
    def current_scene(self):
        return self.__current_scene


class Scene:
    def __init__(self, type):        
        self.type = type
        
        self.name = None
        
        self.game_objects = {}
        
        self.game = None
        
    def add_game_object(self, new_game_object):
    	self.game_objects.update({new_game_object.name:new_game_object})
    	sorted_keys = sorted(self.game_objects)
    	self.game_objects = {key:self.game_objects[key] for key in sorted_keys}
    def remove_game_object(self, old_game_object):
    	self.game_objects.pop(old_game_object.name)
    
    def draw(self):
    	for game_object in self.game_objects.values():
    		game_object.draw(self.game.screen)

    
    def tick(self, delta_time, changed_virtual_screen_position):
        for game_object in self.game_objects.values():
        	game_object.update(delta_time, changed_virtual_screen_position)


class GameObject(pygame.sprite.Sprite):	
	def __init__(self, type, animation_name):
		self.type = type
		self.animation_name = animation_name	
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
	
	def draw(self, screen):
		screen.blit(self.image, self.rect)
	
	def update(self, delta_time, changed_virtual_screen_position):
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
				
		self.rect = self.image.get_rect(x=self.position[0], y=self.position[1])


class Entity(GameObject):
	pass


class Wall(GameObject):
	def update(self, delta_time, changed_virtual_screen_position):
		mouse_pos = self.scene.game.get_mouse_pos()
		
		if self.rect.collidepoint(mouse_pos):
			self.position[0] = random.randint(0, 1316)
			self.position[1] = random.randint(0, 718)
		super().update(delta_time, changed_virtual_screen_position)


class Camera(GameObject):
	def draw(self, screen):
		pass
	
	def set_position(self, new_position):
		self.position = new_position


class TileMap(GameObject):
	tiles_images = {}
	chunks_images = {}
	chunk_size = None
	tile_size = None
	
	def __init__(self, type, animation_name):
		self.tilemap_name = None
		self.tilemap_size = None
		self.map_of_chunks_size = None
		super().__init__(type, animation_name)
		
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
				screen.blit(chunk_image, [chunk_x, chunk_y])
		
	def update(self, delta_time, changed_virtual_screen_position):
		super().update(delta_time, changed_virtual_screen_position)
