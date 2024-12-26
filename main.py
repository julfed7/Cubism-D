import os
import sys
import json
import pygame
import time

def resource_path(relative):
	if hasattr(sys, "_MEIPASS"):
		return os.path.join(sys._MEIPASS, relative)
	return os.path.join(relative)
	
def path(this_path, environtment_os="android"):
	if environtment_os == "windows":
		return resource_path(this_path)
	else:
		return this_path

def read_file_json(path):
	with open(path) as file:
		data = file.read()
		book = json.loads(data)
	return book
	
def read_file(path):
	if "/" in path:
		file_name = path.split("/")[-1]
	else:
		file_name = path.split("\\")[-1]
	file_type = file_name.split(".")[-1]
	if file_type == "json":
		return read_file_json(path)

class Image:
	def __init__(self, path):
		self.path = path
		self.surface = None
	def setup(self):
		self.set_surface(pygame.image.load(path(self.get_path())))
	def get_path(self):
		return self.path
	def set_surface(self, new_surface):
		self.surface = new_surface
	def get_surface(self):
		return self.surface

class Window:
	def __init__(self, width, height):
		self.width = width
		self.height = height
		self.title = "default"
		self.surface = None
		self.icon_image = None
	def setup(self):
		pygame.display.set_mode((self.get_width(), self.get_height()))
		self.set_surface(pygame.display.get_surface())
	def update(self):
		pygame.display.set_mode((self.get_width(), self.get_height()))
		pygame.display.set_caption(self.get_title())
		pygame.display.set_icon(self.get_icon_image().get_surface())
	def set_surface(self, new_surface):
		self.surface = new_surface
	def get_surface(self):
		return self.surface
	def get_width(self):
		return self.width
	def get_height(self):
		return self.height
	def set_title(self, new_title):
		self.title = new_title
	def get_title(self):
		return self.title
	def set_icon_image(self, new_image):
		self.icon_image = new_image
	def get_icon_image(self):
		return self.icon_image

environtment_os = "android"		
		
config = read_file(path("settings/app.json"))

TITLE = config["Title"]

FPS = config["FPS"]

WIDTH = config["Width"]

HEIGHT = config["Height"]

icon_file_name = config["Icon_file_name"]

is_running = True

pygame.init()

window = Window(WIDTH, HEIGHT)
window.setup()

screen = window.get_surface()

window.set_title(TITLE)

icon_image = Image(path("sprites/icon.png"))
icon_image.setup()

window.set_icon_image(icon_image)

window.update()

while is_running:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			is_running = False
		elif event.type == pygame.KEYUP:
			if event.key == pygame.K_ESCAPE:
				is_running = False
	pygame.display.flip()				
pygame.quit()