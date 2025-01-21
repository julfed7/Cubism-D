import time
import utils
import logic
import pygame

ticks = 0

last_time = time.time()
delta_time = last_time/1000

last_screen_orientation = "Landscape"
screen_orientation = "Landscape"

is_running = True

ENVIRONMENT_OS = "Android"		
        
config = utils.read_file(utils.path("settings/app.json"))

TITLE = config["Title"]

FPS = config["FPS"]

WIDTH = config["Width"]

HEIGHT = config["Height"]

ICON_FILE_NAME = config["Icon_file_name"]


screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

virtual_screen = pygame.Surface((WIDTH, HEIGHT))

icon_image = pygame.image.load(utils.path("sprites/"+ICON_FILE_NAME))

pygame.display.set_caption(TITLE)

pygame.display.set_icon(icon_image)


logic.Grass.sprite = pygame.image.load(utils.path("sprites/grass.png"))

screen_size = screen.get_size()

game = logic.Game()

scenes = utils.read_file(utils.path("settings/scenes.json"))

for scene_name in scenes:
    scene_parameters = scenes[scene_name]
    
    new_scene = logic.Scene(scene_name)
    
    for game_object_name in scene_parameters["Game_objects"]:
        game_object_parameters = scene_parameters["Game_objects"][game_object_name]
        
        arguments = {game_object_parameter_name.lower():game_object_parameter_value for game_object_parameter_name, game_object_parameter_value in game_object_parameters.items()}
        
        marks = []

        removing_arguments_name = []
        
        changing_arguments_name = []
        
        for argument_name in arguments:
            if argument_name == "type":
                removing_arguments_name.append(argument_name)
            elif argument_name == "position":
            	changing_arguments_name.append(argument_name)
            elif argument_name == "is_over_screen":
            	removing_arguments_name.append(argument_name)
            	
            	if arguments[argument_name] == True:
            		changing_arguments_name.append("position")
       
            		marks.append("is_over_screen")
        	       		      
        for removing_argument_name in removing_arguments_name:
            arguments.pop(removing_argument_name)
                    
        for changing_argument_name in changing_arguments_name:
        	if changing_argument_name == "position":
        		if "is_over_screen" not in marks:
        			position = [arguments[changing_argument_name][0]*WIDTH, arguments[changing_argument_name][1]*HEIGHT]
        		else:
        			position = [arguments[changing_argument_name][0]*screen_size[0], arguments[changing_argument_name][1]*screen_size[1]]
        		arguments[changing_argument_name] = position
        			
        if "is_over_screen" not in marks:
        	screen_ = virtual_screen
        else:
        	screen_ = screen

        if game_object_parameters["Type"] == "Grass":      	
            game_object = logic.Grass(screen_, game_object_name, **arguments)
            
        for mark in marks:
        	setattr(game_object, mark, None)
        
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
                
    #Before screen draw
    virtual_screen.fill((255, 255, 255))
    
    post_screen_draw_game_objects = []
    
    for game_object in current_scene.game_objects:
        if not hasattr(game_object, "is_over_screen"):
        	game_object.render()
        else:
        	post_screen_draw_game_objects.append(game_object)
    
    #Window
    screen_size = screen.get_size()
    
    last_screen_orientation = screen_orientation
    
    if screen_size[0] > screen_size[1]:
    	screen_orientation = "Landscape"
    else:
    	screen_orientation = "Portret"	
    
    if screen_orientation != last_screen_orientation:
    	screen.fill((0, 0, 0))
    
    if screen_orientation == "Landscape":
    	size = (screen_size[1]/HEIGHT*WIDTH, screen_size[1])
    elif screen_orientation == "Portret":
    	size = (screen_size[0], screen_size[0]/WIDTH*HEIGHT)
    
    changed_virtual_screen = pygame.transform.scale(virtual_screen, size)
    
    screen.blit(changed_virtual_screen, (screen_size[0]/2-size[0]/2, screen_size[1]/2-size[1]/2))
    
    #Post screen draw
    for post_screen_draw_game_object in post_screen_draw_game_objects:    	
    	post_screen_draw_game_object.render()
    	
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
