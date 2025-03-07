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
        
        self.ENVIRONMENT_OS = None
        
        self.TILE_SIZE = None
        
    def setup(self, screen, virtual_screen_size, ENVIRONMENT_OS, TILE_SIZE):
        self.screen = screen
        self.virtual_screen_size = virtual_screen_size
        self.ENVIRONMENT_OS = ENVIRONMENT_OS
        self.TILE_SIZE = TILE_SIZE
        
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

        self.current_camera = None
        
        self.current_player_game_object = None
        
        self.player_game_object_name = None
        
        self.player_controller_game_object = None
        
        self.player_controller_game_object_name = None

    def setup(self):
        if self.player_game_object_name:
        	self.current_player_game_object = self.game_objects[self.player_game_object_name]
        if self.player_controller_game_object_name:
        	self.player_controller_game_object = self.game_objects[self.player_controller_game_object_name]
        
    def add_game_object(self, new_game_object):
        if not new_game_object.is_only_for_smartphones and (self.game.ENVIRONMENT_OS == "Android" or self.game.ENVIRONMENT_OS == "IOS"):
         self.game_objects.update({new_game_object.name:new_game_object})
         sorted_keys = sorted(self.game_objects)
         self.game_objects = {key:self.game_objects[key] for key in sorted_keys}
    def remove_game_object(self, old_game_object):
        self.game_objects.pop(old_game_object.name)
    
    def draw(self):
        offset_position = copy.copy(self.current_camera.position)


        for y in range(math.ceil(self.game.virtual_screen_size[1]/self.game.TILE_SIZE)):
        	for x in range(math.ceil(self.game.virtual_screen_size[0]/self.game.TILE_SIZE)):
        		line_x = -self.current_camera.position[0]+x*self.game.TILE_SIZE
        		if self.current_player_game_object.velocity[0] < 0:
        			if line_x > self.game.virtual_screen_size[0]:
        				line_x = -x*self.game.TILE_SIZE
        		pygame.draw.line(self.game.screen, "gray", [line_x, -self.current_camera.position[1]], [line_x, -self.current_camera.position[1]+self.game.virtual_screen_size[1]])
        		pygame.draw.line(self.game.screen, "gray", [-self.current_camera.position[0], -self.current_camera.position[1]+y*self.game.TILE_SIZE], [-self.current_camera.position[0]+self.game.virtual_screen_size[0], -self.current_camera.position[1]+y*self.game.TILE_SIZE])
        for game_object in self.game_objects.values():
            game_object.draw(self.game.screen)
    
    def tick(self, delta_time, changed_virtual_screen_position):
        for game_object in self.game_objects.values():
            game_object.update(delta_time, changed_virtual_screen_position)
        
        if self.player_controller_game_object_name and self.player_game_object_name:
        	self.current_player_game_object.velocity = self.player_controller_game_object.direction


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
        self.is_only_for_smartphones = False

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

        self.rect = self.image.get_rect(x=self.position[0], y=self.position[1])


class Entity(GameObject):
    def __init__(self, *args):
    	super().__init__(*args)
    	self.speed = 0
    	self.velocity = [0, 0]
    	
    def update(self, *args):
    	super().update(*args)
    	self.position[0] += self.velocity[0] * self.speed * self.delta_time
    	self.position[1] += self.velocity[1] * self.speed * self.delta_time


class Wall(GameObject):
    def update(self, delta_time, changed_virtual_screen_position):
        mouse_pos = self.scene.game.get_mouse_pos()

        if self.rect.collidepoint(mouse_pos):
            self.position[0] = random.randint(0, 1316)
            self.position[1] = random.randint(0, 718)
        super().update(delta_time, changed_virtual_screen_position)


class Camera(GameObject):
    def __init__(self, *args):
       super().__init__(*args)
       self.targeting_game_object = None
       self.mode = None
       self.target_game_object_name = None
    def setup(self):
       super().setup()
       self.targeting_game_object = self.scene.game_objects[self.target_game_object_name]
       
    def draw(self, screen):
        pass
     
    def update(self, *args):
    	super().update(*args)
    	if self.mode == "Focus_at_game_object":
    		self.focus_at_game_object()
    	elif self.mode == "Static":
    		pass

    		
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
                screen.blit(chunk_image, [chunk_x+self.rect.x, chunk_y+self.rect.y])

    def update(self, delta_time, changed_virtual_screen_position):
        super().update(delta_time, changed_virtual_screen_position)

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
	def draw(self, *args):
		pygame.draw.circle(self.scene.game.screen, self.color, [self.position[0], self.position[1]], self.radius, self.border_radius)
		pygame.draw.circle(self.scene.game.screen, self.color, [self.stick_position[0], self.stick_position[1]], self.radius/2)
	def update(self, *args):
		super().update(*args)
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
			
class FpsCounter(GameObject):
	def __init__(self, *args):
		super().__init__(*args)
	def draw(self, *args):
		super().draw(*args)
