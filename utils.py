import json

def read_file_json(path):
	with open(path) as file:
		data = file.read()
		dict_ = json.loads(data.decode())
	return dict_