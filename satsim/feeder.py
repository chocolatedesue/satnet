from websocket_server import WebsocketServer
import json


def message_received(client, server: WebsocketServer, message):
    request = json.loads(message)

    constellation, scenario, frame = request["constellation"], request["scenario"], request["index"]

    if frame < 0:
        print("Sending config...")
        config = json.load(open("config.json"))
        server.send_message(client, json.dumps({
            "type": "config",
            "content": config
        }))
        print("Done.")
        return

    if constellation == "":
        print("Sending empty frame ...")
        server.send_message(client, json.dumps({
            "type": "frame",
            "content": {
                "index": 0,
                "nodes": [],
                "edges": []
            }
        }))
        print("Done.")
        return

    if constellation not in server.cache:
        print("Caching constellation {}...".format(constellation))
        common = json.load(
            open("constellations/{}/common.json".format(constellation)))
        server.cache[constellation] = {"": common}
        print("Done.")

    common = server.cache[constellation][""]
    if scenario == "":
        print("Sending frame {}...".format(frame))
        server.send_message(client, json.dumps({
            "type": "frame",
            "content": {
                "index": frame,
                "nodes": common["nodes"][frame],
                "edges": common["edges"]
            }
        }))
        print("Done.")
        return

    if scenario not in server.cache[constellation]:
        print("Caching scenario {}...".format(scenario))
        scenarioExtension = json.load(
            open("constellations/{}/{}.json".format(constellation, scenario)))
        server.cache[constellation][scenario] = scenarioExtension
        print("Done.")

    print("Sending frame {}...".format(frame))
    scenarioExtension = server.cache[constellation][scenario]
    server.send_message(client, json.dumps({
        "type": "frame",
        "content": {
            "index": frame,
            "nodes": common["nodes"][frame] + scenarioExtension[frame]["nodes"],
            "edges": common["edges"] + scenarioExtension[frame]["edges"]
        }})
    )
    print("Done.")


def cacheConstellations(cache):
    config = json.load(open("config.json"))
    for constellation in config.keys():
        print("Caching constellation {}".format(constellation))
        common = json.load(
            open("constellations/{}/common.json".format(constellation)))
        cache[constellation] = {"": common}
        print("Done.")


if __name__ == "__main__":
    server = WebsocketServer(host='192.168.1.105', port=8282)
    server.cache = {}
#    cacheConstellations(server.cache)
    server.set_fn_message_received(message_received)
    server.run_forever()
