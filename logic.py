class Game:
    def __init__(self):
        self.__scenes = []
        self.__current_scene = 0
    def tick(self):
        self.get_scene().tick()
    def get_scene(self):
        return self.scenes[self.current_scene]
    def add_scene(self, new_scene):
        self.scenes.append(new_scene)
    @property
    def scenes(self):
        return self.__scenes
    @property
    def current_scene(self):
        return self.__current_scene
        
    

class Scene:
    def __init__(self):
        self.__game_objects = []
    def tick(self):
        for game_object in self.game_objects:
            game_object.tick()
    def add_game_object(self, new_game_object):
        self.game_objects.append(new_game_object)
    def del_game_object(self, game_object_or_index):
        if isinstance(game_object_or_index, GameObject):
            self.game_objects.remove(game_object_or_index)
        else:
            self.game_objects.remove(self.game_objects[game_object_or_index])
    @property
    def game_objects(self):
        return self.__game_objects

class GameObject:
    def __init__(self):
        pass
    def tick(self):
        pass