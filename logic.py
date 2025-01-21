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
    def del_scene(self, scene_name):
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
        self.game_objects = []
    def tick(self):
        for game_object in self.game_objects:
            game_object.tick()


class Grass:
    sprite = None
    def __init__(self, screen, name, position):
        self.__screen = screen
        self.name = name
        self.position = position
    def render(self):
    	self.screen.blit(Grass.sprite, (self.position[0], self.position[1]))
    @property
    def screen(self):
    	return self.__screen
