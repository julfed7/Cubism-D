class Game:
    def __init__(self):
        self.scenes = []
        self.current_scene = 0
    def tick(self):
        self.get_scene().tick()
    def get_scene(self):
        return self.scenes[self.current_scene]

class Scene:
    def __init__(self):
        self.game_objects = []
    def tick(self):
        for game_object in self.get_game_objects():
            game_object.tick()
    def get_game_objects(self):
        return self.game_objects

class GameObject:
    def __init__(self):
        pass
    def tick(self):
        pass