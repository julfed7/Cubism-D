import json
import utils
import pygame

config = utils.read_file_json("C:\Users\Ученик\Desktop\Федотов Дьулустан 10А\video games\cubism d\settings\app.json")

TITLE = config["Title"]

FPS = config["FPS"]

WIDTH = config["Width"]

HEIGHT = config["Height"]

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))

clock = pygame.time.Clock()

is_running = True

while is_running:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			is_running = False
	pygame.display.flip()
	clock.tick(FPS)
pygame.quit()