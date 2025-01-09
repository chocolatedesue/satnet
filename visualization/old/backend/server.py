from websocket_server import WebsocketServer
import json
import math
import os

def message_received(client, server: WebsocketServer, message):
    request = json.loads(message)

    if request["action"] == "open":
        print("Sending config...")
        config = json.load(open("config.json"))
        server.send_message(client, json.dumps({
            "type": "config",
            "content": config["config"]
        }))
        print("Done.")

    if request["action"] == "request_frame":
        scenario = request["scenario"]
        algorithm = request["algorithm"]
        frame_id = request["frame_id"]
        print("Request received: ", [scenario, algorithm, frame_id])
        frame_key = ' - '.join([scenario, algorithm, str(frame_id)])
        print("Frame Key: ", frame_key)
        if frame_key in server.frame_cache:
            print("Hit.")
            frame = server.frame_cache[frame_key]
        else:
            print("Miss.")
            frame = server.frame_cache["default - " + str(frame_id)]
        msg = json.dumps({ "type" : "frame", "content" : frame})
        server.send_message(client, msg)

def load(filename, prefix, cache):
    f = open(filename)
    lines = f.readlines()
    for i in range(0, 60):
        nodeStrList = lines[i * 2].split('|')
        nodeList = []
        for nodeStr in nodeStrList:
            x, y, attri = nodeStr.strip().split(' ')
            nodeList.append([float(x), float(y), int(attri)])
        edgeStrList = lines[i * 2 + 1].split('|')
        edgeList = []
        for edgeStr in edgeStrList:
            u, v, attri = edgeStr.strip().split(' ')
            edgeList.append([int(u), int(v), int(attri)])
        cache[prefix + str(i)] = { "id" : i, "nodes" : nodeList, "edges" : edgeList }

if __name__ == "__main__":
    server = WebsocketServer(host='192.168.1.14', port=9527)
    print("Caching...")
    server.frame_cache = {}
    loadDir = "../frame_data"
    for filename in json.load(open("config.json"))["file_list"]:
        filepath = os.path.join(loadDir, filename)
        keyprefix = filename.split('.')[0] + " - "
        load(filepath, keyprefix, server.frame_cache)
    print("Cache Done.")
    server.set_fn_message_received(message_received)
    server.run_forever()
