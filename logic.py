import utils
import pygame


class Game:
    def __init__(self):
        self.__scenes = {}
        
        self.__current_scene = 0
        
    def tick(self):
        self.get_scene().tick()
        
    def get_scene(self):
        return list(self.scenes.values())[self.current_scene]
        
    def add_scene(self, new_scene):
        self.scenes.update({new_scene.name:new_scene})
        
    def remove_scene(self, scene_name):
        self.scenes.pop(scene_name)
        
    @property
    def scenes(self):
        return self.__scenes
        
    @property
    def current_scene(self):
        return self.__current_scene        


class Scene:
    def __init__(self, name):
        self.name = name
        
        self.game_objects = pygame.sprite.Group()
        
    def add_game_object(self, new_game_object):
    	self.game_objects.add(new_game_object)
    	
    def remove_game_object(self, old_game_object):
    	self.game_objects.remove(old_game_object)
    	
    def tick(self):
        self.game_objects.update()


class Grass(pygame.sprite.Sprite):
    image = None
    
    def __init__(self, name, position):
        self.name = name
        
        self.position = position
        
        self.image = Grass.image
        
        self.rect = self.image.get_rect(x=self.position[0], y=self.position[1])
 
 
class PeaShooter(pygame.sprite.Sprite):
	animation_name "peashooter"
	
	__animation_ticks = [3, 4, 4, 4, 4, 3, 4, 4, 4, 4, 3, 4, 4, 4, 4, 3]
	
	animation_frame_images = []
	
	def __init__(self, name, position):
		self.name = name
		
		self.position = position
		
		self.__ticks = 0
		
		self.image = PeaShooter.animation_frame_images[animation_current_frame]
		
		self.rect = self.image.get_rect(x=self.position[0], y=position[1])
		
		self.__animation_current_frame = 0
		
		self.__last_frame_flip_ticks = self.ticks
		
	def update(self):
		if ticks-last_frame_flip_ticks > 
		self.animation_current_frame += 1
		
		self.image = PeaShooter.animation_frame_images[self.animation_current_frame]
	
	@property
	def animation_current_frame(self):
		return self.__animation_current_frame
	
	@property
	def animation_ticks(self):
		return self.__animation_ticks
		
	@property
	def ticks(self):
		return self.__ticks
		
	@property
	def last_frame_flip_ticks(self):
		return self.__last_frame_flip_ticks
