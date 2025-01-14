import sys
import os
import json

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
