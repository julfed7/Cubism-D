import socket
import threading
import json
import random
import time
import numpy

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("localhost", 2222))
s.setblocking(0)
s.listen(1)

connections = []

game_objects = []

game_started = False

hub = []

class Player:
    def __init__(self, player_id, x, y, name="player"):
        self.type = "player"
        self.name = name
        self.id = player_id
        self.position = numpy.array([x, y])
    def tick(self):
        pass

def create_response(type=None, data=None, id=None):
    response = {
        "response": type,
        "data": data,
        "id": id
    }
    return response.copy()

def create_request(type=None, data=None, id=None):
    request = {
        "request": type,
        "data": data,
        "id": id
    }
    return request.copy()

def get_id(connection):
    if connection in connections:
        return connection["id"]
    else:
        return False

def get_connection(id):
    for connection in connections:
        if not id:
            return connection
        elif connection["id"] == id:
            return connection
        else:
            return connections[-1]

def get_object(id):
    for game_object in game_objects:
        if not id:
            return game_object
        elif game_object.id == id:
            return game_object
        else:
            return game_objects[-1]

def remove_connection(id):
    connection = get_connection(id)
    connections.remove(connection)
    return True

def remove_object(id):
    game_object = get_object(id)
    game_objects.remove(game_object)
    return True

def get_is_type_in(type):
    for game_object in game_objects:
        if game_object.type == type:
            return True
    return False

def request_sender(data):
    connection = get_connection(data["id"])
    request_ = json.dumps(data)
    request_ = request_.encode()
    if connection:
        connection["request_queue"].append(request_)
    return True

def response_sender(data):
    connection = get_connection(data["id"])
    connection["response_queue"].append(data)
    return True

def response_connect(data):
    client_id = connections[-1]["id"]
    response = create_response("get_id", client_id, client_id)
    request_sender(response)
    return True

def response_disconnect(data):
    response = create_response("get_access_to_exit", True, data["id"])
    if request_sender(response):
        time.sleep(1)
        remove_connection(data["id"])
        try:
            remove_object(data["id"])
        except:
            pass
        try:
            hub.remove(data["id"])
        except:
            pass
    return True

def response_pinged(data):
    connection = get_connection(data["id"])
    connection["pinged"] = True
    return True

def response_joined(data):
    global hub
    try:
        hub.remove(data["id"])
    except:
        pass

def response_join_to_game(data):
    global hub, game_started, game_objects
    if len(hub) >= 2 and not game_started:
        print("game started")
        game_started = True
        print(hub)
        for id in hub:
            print("new object Type: player")
            request = create_request("join_to_game", None, id)
            request_sender(request)
            player = Player(id, random.randint(0, 1280), random.randint(0, 720))
            game_objects.append(player)
            print(game_objects)
        return True
    elif game_started:
        request = create_request("join_to_game", None, data["id"])
        request_sender(request)
        return True
    return False

def response_join_to_play(data):
    global hub
    if data["id"] not in hub and not game_started:
        print("joining to hub...")
        hub.append(data["id"])
        response = create_response("get_access_to_hub", None, data["id"])
        request_sender(response)
        print("joined to hub", data["id"])
        print(hub)
        response_join_to_game(data)
    else:
        response = create_response("get_error_disconnect_game_started", None, data["id"])
        request_sender(response)
    return True

def response_online(data):
    global hub
    response = create_response("get_online", len(hub), data["id"])
    request_sender(response)
    return True

def response_objects(data):
    objects = []
    for game_object in game_objects:
        object = {"id": game_object.id, "type": game_object.type, "x": int(game_object.position[0]), "y": int(game_object.position[1])}
        objects.append(object)
    print(game_objects)
    response = create_response("get_objects", objects, data["id"])
    request_sender(response)
    return True

def response_leave_hub(data):
    response = create_response("get_access_to_leave_hub", True, data["id"])
    if request_sender(response):
        time.sleep(1)
        try:
            hub.remove(data["id"])
        except:
            pass
        return True

messages = {
    "response": {
        "pinged": response_pinged,
        "joined": response_joined
    },
    "request": {
        "connect": response_connect,
        "disconnect": response_disconnect,
        "join_to_play": response_join_to_play,
        "online": response_online,
        "objects": response_objects,
        "leave_hub": response_leave_hub
    }
}

def message_caller(data):
    messages[list(data.keys())[0]][list(data.values())[0]](data)
    return True

def connect_handler():
    print("\nworker: connect handler started", end="")
    while True:
        if not server_is_alive:
            return
        try:
            conn, addr = s.accept()
            conn.setblocking(0)
            connections.append({"conn": conn, "addr": addr, "id": random.randint(0,10000), "pinged": True, "response_queue": [], "request_queue": []})
        except OSError:
            pass
        time.sleep(1)

def data_handler():
    print("\nworker: data handler started", end="")
    while True:
        if not server_is_alive:
            return
        if connections:
            for connection in connections:
                try:
                    data = connection["conn"].recv(1024)
                    data = data.decode()
                    response = json.loads(data)
                    response_sender(response)
                except:
                    pass
        time.sleep(0.0166666666666667)

def response_handler():
    print("\nworker: response handler started", end="")
    while True:
        if not server_is_alive:
            return
        if connections:
            for connection in connections:
                if connection["response_queue"]:
                    for message in connection["response_queue"]:
                        message_caller(message)
                        connection["response_queue"].remove(message)
                        print("getted", message)
        time.sleep(0.0166666666666667)

def request_handler():
    print("\nworker: request handler started", end="")
    while True:
        if not server_is_alive:
            return
        if connections:
            for connection in connections:
                if connection["request_queue"]:
                    for message in connection["request_queue"]:
                        connection["conn"].send(message)
                        connection["request_queue"].remove(message)
                        print("sended", message)
        time.sleep(0.0166666666666667)

def connection_pinger():
    print("\nworker: connection pinger started", end="")
    while True:
        if not server_is_alive:
            return
        if connections:
            time.sleep(10)
            for connection in connections:
                if not connection["pinged"]:
                    remove_connection(connection["id"])
                else:
                    connection["pinged"] = False
                request = create_request("ping", None, connection["id"])
                request_sender(request)

def objects_tick():
    print("\nworker: objects tick started", end="")
    while True:
        if not server_is_alive:
            return
        if game_objects and game_started:
            for game_object in game_objects:
                game_object.tick()
        time.sleep(0.0166666666666667)

def game_restarter():
    global game_started, game_objects
    print("\nworker: game restarter started", end="")
    while True:
        if not server_is_alive:
            return
        if game_started:
            isHavePlayerInGame = False
            time.sleep(5)
            for game_object in game_objects:
                if game_object.type == "player":
                    isHavePlayerInGame = True
            if not isHavePlayerInGame:
                print("game restarted")
                game_started = False
                game_objects = []
            else:
                print("game not restarted")
                print(game_objects)


def main():
    global server_is_alive
    server_is_alive = True
    print("workers starting...", end="")
    threads0 = []
    thread0 = threading.Thread(target=connect_handler)
    thread1 = threading.Thread(target=data_handler)
    thread2 = threading.Thread(target=response_handler)
    thread3 = threading.Thread(target=request_handler)
    thread4 = threading.Thread(target=connection_pinger)
    thread5 = threading.Thread(target=objects_tick)
    thread6 = threading.Thread(target=game_restarter)
    threads0.append(thread0)
    threads0.append(thread1)
    threads0.append(thread2)
    threads0.append(thread3)
    threads0.append(thread4)
    threads0.append(thread5)
    threads0.append(thread6)
    for thread in threads0:
        thread.start()
    print("\nall workers started!", "(", len(threads0), ")")
    print("server started")
    thread3.join()
    server_is_alive = False
    print("server died")
    print(time.ctime())

if __name__ == "__main__":
    main()
