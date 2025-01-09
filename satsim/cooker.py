from websocket_server import WebsocketServer
import json
import traceGenerator

def message_received(client, server: WebsocketServer, message):
    request = json.loads(message)

    constellation, scenario, index = request["constellation"], request["scenario"], request["index"]

    if index < 0:
        print("Sending config...")
        config = json.load(open("config.json"))
        for value in config.values():
            value["numframes"] = 24 * 60 * 60
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

    tgconfig = json.load(open("tgconfig.json"))
    common = traceGenerator.generateTopo([constellation, "", index], tgconfig)
    if scenario == "":
        print("Sending frame {}...".format(index))
        server.send_message(client, json.dumps({
            "type": "frame",
            "content": {
                "index": index,
                "nodes": common["nodes"],
                "edges": common["edges"]
            }
        }))
        print("Done.")
        return

    print("Sending frame {}...".format(index))
    scenarioExtension = traceGenerator.generateScenario(
                    [constellation, scenario, index], tgconfig)
    server.send_message(client, json.dumps({
        "type": "frame",
        "content": {
            "index": index,
            "nodes": common["nodes"] + scenarioExtension["nodes"],
            "edges": common["edges"] + scenarioExtension["edges"]
        }})
    )
    print("Done.")

if __name__ == "__main__":
    server = WebsocketServer(host='192.168.1.14', port=8283)
    server.cache = {}
    server.set_fn_message_received(message_received)
    server.run_forever()
