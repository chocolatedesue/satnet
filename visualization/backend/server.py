from websocket_server import WebsocketServer
import json
import math
import os

portNum = 12311
# loadDirs = ["/home/chenyuxuan/satnet/visualization/frame_data", "/home/linrunbo/satvis-minimal/visualization/frame_data", "/home/phye/satvis-minimal/visualization/frame_data"]
loadDirs = [
    "visualization/frame_data/"
]
defaultFrame = {
    "id" : -1, "nodes" : [], "edges" : [], "nodes_3d" : [], "num_frames" : 0
}

def getConfig():
    config = {}
    for loadDir in loadDirs:
        name_list = os.listdir(loadDir)
        name_list.sort()
        for name in name_list:
            spath = os.path.join(loadDir, name)
            if os.path.isdir(spath):
                scenario, algorithm = name.split(' - ')
                if scenario not in config:
                    config[scenario] = []
                if algorithm:
                    config[scenario].append(algorithm)
    return config

def message_received(client, server: WebsocketServer, message):
    request = json.loads(message)

    if request["action"] == "open":
        print("Sending config...")
        server.send_message(client, json.dumps({
            "type": "config",
            "content": getConfig()
        }))
        print("Done.")

    if request["action"] == "request_frame":
        scenario = request["scenario"]
        algorithm = request["algorithm"]
        frame_id = request["frame_id"]
        print("Request received: ", [scenario, algorithm, frame_id])
        frame_key = ' - '.join([scenario, algorithm])
        print("Frame Key: ", frame_key)
        flag = False
        for loadDir in loadDirs:
            frame_path = os.path.join(loadDir, frame_key, "{}.txt".format(frame_id))
            if os.path.exists(frame_path):
                print("Hit.")
                flag = True
                nodeList, edgeList, node3dList = load(frame_path)
                num_frames = len(os.listdir(os.path.join(loadDir, frame_key)))
                frame = {
                    "id": frame_id,
                    "nodes": nodeList,
                    "edges": edgeList,
                    "nodes_3d": node3dList,
                    "num_frames": num_frames
                }
                break
        
        if not flag:
            print("Miss.")
            frame = defaultFrame
        msg = json.dumps({ "type" : "frame", "content" : frame})
        server.send_message(client, msg)

def load(filename):
    f = open(filename)
    lines = f.readlines()
    nodeStrList = lines[0].split('|')
    nodeList = []
    for nodeStr in nodeStrList:
        x, y, attri = nodeStr.strip().split(' ')
        nodeList.append([float(x), float(y), int(attri)])
    edgeStrList = lines[1].split('|')
    edgeList = []
    for edgeStr in edgeStrList:
        u, v, attri = edgeStr.strip().split(' ')
        edgeList.append([int(u), int(v), int(attri)])
    node3dList = []
    if len(lines) > 2:
        node3dStrList = lines[2].split('|')
        for node3dStr in node3dStrList:
            x, y, z = node3dStr.strip().split(' ')
            node3dList.append([float(x), float(y), float(z)])
    
    return nodeList, edgeList, node3dList

if __name__ == "__main__":
    # server = WebsocketServer(host='192.168.1.14', port=portNum)
    server = WebsocketServer(host='127.0.0.1', port=portNum)
    server.set_fn_message_received(message_received)
    server.run_forever()
