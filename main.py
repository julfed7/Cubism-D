import time
import utils
import logic
import pygame

ticks = 0

last_time = time.time()
delta_time = last_time/1000

is_running = True

ENVIRONMENT_OS = "Android"		
        
config = utils.read_file(utils.path("settings/app.json"))

TITLE = config["Title"]

FPS = config["FPS"]

WIDTH = config["Width"]

HEIGHT = config["Height"]

PROPORTION_X = config["Proportion_x"]

PROPORTION_Y = config["Proportion_y"]

ICON_FILE_NAME = config["Icon_file_name"]


screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

virtual_screen = pygame.Surface((WIDTH, HEIGHT))

icon_image = pygame.image.load(utils.path("sprites/"+ICON_FILE_NAME))

pygame.display.set_caption(TITLE)

pygame.display.set_icon(icon_image)


sprites = {
    logic.Grass: pygame.image.load(utils.path("sprites/grass.png"))
}


game = logic.Game()

scenes = utils.read_file(utils.path("settings/scenes.json"))

for scene_name in scenes:
    scene_parameters = scenes[scene_name]
    
    new_scene = logic.Scene(scene_name)
    
    for game_object_name in scene_parameters["Game_objects"]:
        game_object_parameters = scene_parameters["Game_objects"][game_object_name]
        
        arguments = {game_object_parameter_name.lower():game_object_parameter_value for game_object_parameter_name, game_object_parameter_value in game_object_parameters.items()}

        removing_arguments_name = []
        
        for argument_name in arguments:
            if argument_name == "type":
                removing_arguments_name.append(argument_name)

        for removing_argument_name in removing_arguments_name:
            arguments.pop(removing_argument_name)

        if game_object_parameters["Type"] == "Grass":
            game_object = logic.Grass(game_object_name, **arguments)
        
        new_scene.game_objects.append(game_object)
 
    game.add_scene(new_scene)


current_scene = game.get_scene()

while is_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE:
                is_running = False
    #Draw
    virtual_screen.fill((255, 255, 255))
    
    surface = pygame.Surface((50, 50))
    surface.fill("yellow")
    virtual_screen.blit(surface, (1316, 0))

    for game_object in current_scene.game_objects:
        virtual_screen.blit(sprites[type(game_object)], (game_object.position[0], game_object.position[1]))
    

    #Window
    screen_size = screen.get_size()
    
    size = (screen_size[0]/PROPORTION_X*PROPORTION_Y, screen_size[1])
    
    changed_virtual_screen = pygame.transform.scale(virtual_screen, size)
    
    screen.blit(changed_virtual_screen, (screen_size[0]/2-size[0]/2, screen_size[1]/2-size[1]/2))
    
    pygame.display.flip()


    #FPS
    ticks += 1
    
    delta_time = time.time()-last_time
    
    last_time = time.time()
    
    sleep_time = 1/FPS - delta_time
    
    if sleep_time < 0:
        sleep_time = 0
        
    time.sleep(sleep_time)


pygame.quit()
