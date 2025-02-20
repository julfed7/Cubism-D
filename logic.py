import utils
import pygame


class Game:
    def __init__(self):
        self.__scenes = {}
        
        self.__current_scene = 0
        
        self.screen  = None
        
    def setup(self, screen):
        self.screen = screen
        
    def render(self):
        scene = self.get_scene()
        
        scene.draw()
        
    def tick(self, delta_time):
        self.get_scene().tick(delta_time)
        
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
    def __init__(self, type):        
        self.type = type
        
        self.name = None
        
        self.game_objects = {}
        
        self.game = None
        
    def add_game_object(self, new_game_object):
    	self.game_objects.add(new_game_object)
    	
    def remove_game_object(self, old_game_object):
    	seld.game_objects.remove(old_game_object)
    
    def draw(self):
    	for game_object in self.game_objects.values():
    		game_object.draw(self.game.screen)
    
    def tick(self, delta_time):
        for game_object in self.game_objects.values():
        	game_object.update(delta_time)


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
	
	def update(self, delta_time):
		self.rect.x = self.position[0] - self.camera.position[0]
		self.rect.y = self.position[1] - self.camera.position[1]
			
		self.image = self.animation_frame_images[self.state][self.animation_current_frame]
			
		if self.ticks-self.last_frame_flip_ticks == self.animation_ticks[self.state][self.animation_current_frame]-1:
			if self.animation_current_frame + 1 > len(self.animation_frame_images[self.state]) - 1:
				self.animation_current_frame = 0
			else:
				self.animation_current_frame += 1
				
			self.last_frame_flip_ticks = self.ticks
		
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
				
				self.animation_frame_images[animation_state].append(frame_image)
				
		self.image = self.animation_frame_images[self.state][self.animation_current_frame]
				
		self.rect = self.image.get_rect()


class CommonScene(Scene):
	pass


class Entity(GameObject):
	pass


class Wall(GameObject):
	pass


class Camera(GameObject):
	def set_position(self, new_position):
		self.position = new_position





class Grass(pygame.sprite.Sprite):
    image = None
    
    camera = None
    
    def __init__(self, name, position):
        self.name = name
        self.position = position
        self._image = Grass.image
        self._rect = None
        
    def update(self):
        self.rect.x = self.position[0] - Grass.camera.position[0]
        self.rect.y = self.position[1] - Grass.camera.position[1]
        
    def setup(self):
        super().__init__()
        
        self.rect = self.image.get_rect(x=self.position[0], y=self.position[1])
        	
    @property
    def image(self):
        return self._image
        
    @property
    def rect(self):
    	return self._rect
    
    @rect.setter
    def rect(self, new_rect):
    	self._rect = new_rect
 
 
 
 
class PeaShooter(pygame.sprite.Sprite):
	animation_ticks = None
	
	animation_frame_images = []
	
	camera = None
	
	def __init__(self, name, position):
		self.name = name
		
		self.position = position
		
		self.__ticks = 0
		
		self._image = None
		
		self._rect = None
		
		self.__animation_current_frame = 0
		
		self.__last_frame_flip_ticks = self.ticks
		
	def update(self):
		self.rect.x = self.position[0] - PeaShooter.camera.position[0]
		self.rect.y = self.position[1] - PeaShooter.camera.position[1]
		
		if self.ticks-self.last_frame_flip_ticks == PeaShooter.animation_ticks[self.animation_current_frame]-1:
			if self.animation_current_frame + 1 > len(PeaShooter.animation_frame_images) - 1:
				self.animation_current_frame = 0
			else:
				self.animation_current_frame += 1
			
			self.last_frame_flip_ticks = self.ticks
		
		self.image = PeaShooter.animation_frame_images[self.animation_current_frame]
		
		self.ticks += 1
		
	def setup(self):
		super().__init__()
		
		self.image = PeaShooter.animation_frame_images[self.animation_current_frame]
		
		self.rect = self.image.get_rect(x=self.position[0], y=self.position[1])
		
	@property
	def ticks(self):
		return self.__ticks
		
	@ticks.setter
	def ticks(self, new_ticks):
		self.__ticks = new_ticks
		
	@property
	def last_frame_flip_ticks(self):
		return self.__last_frame_flip_ticks
		
	@last_frame_flip_ticks.setter
	def last_frame_flip_ticks(self, new_ticks):
		self.__last_frame_flip_ticks = new_ticks
		
	@property
	def image(self):
		return self._image
	
	@image.setter
	def image(self, new_image):
		self._image = new_image
		
	@property
	def rect(self):
		return self._rect
		
	@rect.setter
	def rect(self, new_rect):
		self._rect = new_rect
		
	@property
	def animation_current_frame(self):
		return self.__animation_current_frame
		
	@animation_current_frame.setter
	def animation_current_frame(self, new_animation_current_frame):
		self.__animation_current_frame = new_animation_current_frame