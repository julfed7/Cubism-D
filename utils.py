import sys
import os
import json
import pygame
import math
import asyncio
from functools import wraps

def resource_path(relative):
  if hasattr(sys, "_MEIPASS"):
    return os.path.join(sys._MEIPASS, relative)
  return os.path.join(relative)

def path(this_path, environment_os="Android"):
  if environment_os == "Windows":
    return resource_path(this_path)
  else:
    return this_path

def read_file_json(path):
  with open(path) as file:
    data = file.read()
    dictionary = json.loads(data)
  
  return dictionary

def read_file(path):
  if "/" in path:
    file_name = path.split("/")[-1]
  else:
    file_name = path.split("\\")[-1]
  
  file_type = file_name.split(".")[-1]
  
  if file_type == "json":
    return read_file_json(path)

def memory(func):
	cache = {}
	@wraps(func)
	def wrapper(*args, **kwargs):
		key = str(args)
		
		if key not in cache:
			cache[key] = func(*args, **kwargs)
		return cache[key]
	return wrapper

@memory
def get_visible_chunks(player_chunk_x, player_chunk_y, chunk_distance_fov, map_of_chunks_size, chunks):
        	visible_chunks = []
        	for i in range(chunk_distance_fov*2+1):
        		point1 = player_chunk_x+player_chunk_y*map_of_chunks_size-chunk_distance_fov-(chunk_distance_fov-i)*map_of_chunks_size
        		point2 = player_chunk_x+player_chunk_y*map_of_chunks_size+chunk_distance_fov-(chunk_distance_fov-i)*map_of_chunks_size
        		visible_chunks += chunks[point1:point2+1]
        	return visible_chunks

@memory
def get_here_chunk(player_chunk_x, player_chunk_y, chunks, map_of_chunks_size):
	try:
		return chunks[player_chunk_x+player_chunk_y*map_of_chunks_size]
	except IndexError:
		return chunks[0]

@memory
def get_entity_rects(entities):
	return [entity.rect for entity in entities.values()]

@memory	
def multiplication(*numbers):
	sum = 1
	for number in numbers:
		sum *= number
	return sum

@memory	
def get_chunk_position(chunk_id, map_of_chunks_size, chunk_size, tile_size):
	chunk_x = chunk_id%map_of_chunks_size*chunk_size*tile_size
	chunk_y = chunk_id//map_of_chunks_size*chunk_size*tile_size
	return chunk_x, chunk_y

@memory
def get_camera_position(position, rect, virtual_screen_size):
	x = position[0]-virtual_screen_size[0]/2+rect.width/2
	y = position[1]-virtual_screen_size[1]/2+rect.height/2
	return [x, y]

@memory
def get_button_text_position(position, button_size, text_size):
	x = position[0] + button_size[0]/2 - text_size[0]/2
	y = position[1] + button_size[1]/2 - text_size[1]/2
	return [x, y]

@memory
def get_joystick_direction(position, mouse_position):
	angle = math.atan2(mouse_position[1]-position[1], mouse_position[0]-position[0])
	vector_x = math.cos(angle)
	vector_y = math.sin(angle)
	lenght = math.sqrt((position[0]-mouse_position[0])**2+(position[1]-mouse_position[1])**2)
	return angle, vector_x, vector_y, lenght
