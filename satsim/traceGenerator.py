
import json
import math
import os


class SatelliteModel:
    def __init__(self, constellationConfig) -> None:
        altitude, inclination, self.Q, self.P = constellationConfig
        self.a = math.radians(inclination)
        self.F = 1
        G = 6.67 * 1e-11
        M = 5.965 * 1e24
        R = (6371.393 + altitude) * 1e3
        self.We = 2 * math.pi / (24 * 60 * 60)
        self.Ws = math.sqrt(G * M / math.pow(R, 3))
        self.altitude = altitude

    def size(self):
        return self.P * self.Q

    def normalize(self, x):
        while x >= math.pi:
            x -= 2 * math.pi
        while x < -math.pi:
            x += 2 * math.pi
        return x

    def phaseDescending(self, x):
        return x >= math.pi / 2 or x < -math.pi / 2

    def getCoord(self, t, i, j):
        u = self.normalize(self.Ws * t + 2 * math.pi / self.Q *
                           j + 2 * math.pi * self.F / self.Q / self.P * i)
        ld = math.atan(math.cos(self.a) * math.tan(u)) + \
            (math.pi if self.phaseDescending(u) else 0)
        x = self.normalize(2 * math.pi / self.P * i - self.We * t + ld)
        y = math.asin(math.sin(self.a) * math.sin(u))
        return [x, y]

    def satDescending(self, t, idx):
        i = idx // self.Q
        j = idx % self.Q
        u = self.normalize(self.Ws * t + 2 * math.pi / self.Q *
                           j + 2 * math.pi * self.F / self.Q / self.P * i)
        return self.phaseDescending(u)

    def getPhi(self, t, idx):
        i = idx // self.Q
        j = idx % self.Q
        u = self.normalize(self.Ws * t + 2 * math.pi / self.Q *
                           j + 2 * math.pi * self.F / self.Q / self.P * i)
        y = math.asin(math.sin(self.a) * math.sin(u))
        return y

    def genTopology(self, t):
        topo = {"nodes": [], "edges": []}
        for i in range(self.P):
            for j in range(self.Q):
                x, y = self.getCoord(t, i, j)
                topo["nodes"].append({
                    "name": "Sat_" + str(i + 1) + "_" + str(j + 1),
                    "coordinates": [math.degrees(x), math.degrees(y), self.altitude],
                    "color": "black"
                })
        for i in range(self.P):
            for j in range(self.Q):
                cur = i * self.Q + j
                bottom = i * self.Q + (j + 1) % self.Q
                r = (i + 1) % self.P
                right = r * self.Q + (j if r > 0 else (j + self.F) % self.Q)
                topo["edges"].append({
                    "endpoints": [cur, bottom],
                    "color": "blue",
                    "dashline": True
                })
                topo["edges"].append({
                    "endpoints": [cur, right],
                    "color": "purple",
                    "dashline": True
                })
        return topo

    def genCartesianCoord(self, coord):
        x, y, z = coord
        r = z + 6371.393
        return [math.cos(y) * math.cos(x) * r, math.cos(y) * math.sin(x) * r, math.sin(y) * r]

    def queryNearest(self, location, t):
        queryCoord = self.genCartesianCoord(location)
        satDists = []
        for i in range(self.P):
            for j in range(self.Q):
                satCoord = self.genCartesianCoord(
                    self.getCoord(t, i, j) + [self.altitude])
                satDists.append(math.dist(queryCoord, satCoord))
        return satDists.index(min(satDists))

    def genRoute(self, src, dst):
        if src < dst:
            src, dst = dst, src

        routes = []
        P, Q, F = self.P, self.Q, self.F
        left = (src // Q - dst // Q) + abs(src % Q - dst % Q)
        right = (P + dst // Q - src // Q) + abs((src % Q + F) % Q - dst % Q)

        cur = src
        if left < right:
            while cur // Q > dst // Q:
                routes.append([cur, cur - Q])
                cur -= Q
        else:
            while cur // Q < P - 1:
                routes.append([cur, cur + Q])
                cur += Q
            routes.append([cur, ((cur % Q) + F) % Q])
            cur = ((cur % Q) + F) % Q
            while cur // Q < dst // Q:
                routes.append([cur, cur + Q])
                cur += Q

        for t in range(min(cur, dst), max(cur, dst)):
            routes.append([t, t + 1])

        return [{"endpoints": route, "color": "red", "dashline": False} for route in routes]

    def moveHorizontally(self, cur, hd):
        assert(hd in [0, -1, 1])
        P, Q, F = self.P, self.Q, self.F
        if cur // Q == P - 1 and hd == 1:
            return (cur + Q + F) % Q
        if cur // Q == 0 and hd == -1:
            return (P - 1) * Q + (cur - Q - F) % Q
        return cur + Q * hd

    def moveVertically(self, cur, vd):
        assert(vd in [0, -1, 1])
        P, Q, F = self.P, self.Q, self.F
        return (cur // Q) * Q + (cur % Q + vd) % Q

    def minHopCount(self, src, dst, s):
        P, Q, F = self.P, self.Q, self.F
        best_direction = None
        min_hop_count = -1
        
        for hor_direction in [-1, 1]:
            for ver_direction in [-1, 1]:
                cur = src
                hor_hop_count = 0
                ver_hop_count = 0
                while cur // Q != dst // Q:
                    cur = self.moveHorizontally(cur, hor_direction)
                    hor_hop_count += 1
                while cur % Q != dst % Q:
                    cur = self.moveVertically(cur, ver_direction)
                    ver_hop_count += 1
                assert(cur == dst)
                hop_count = hor_hop_count + ver_hop_count
                if best_direction == None or hop_count < min_hop_count:
                    best_direction = [hor_direction, ver_direction]
                    min_hop_count = hop_count
                    Hh = hor_hop_count
                    Hv = ver_hop_count
        
        hd, vd = best_direction[0], best_direction[1]
        hcur = src

        for _ in range(Hh + 1):
            vcur = hcur
            vlist = []
            for _ in range(Hv + 1):
                vlist.append(vcur)
                vcur = self.moveVertically(vcur, vd)
            s.append(vlist)
            hcur = self.moveHorizontally(hcur, hd)

        return Hh, Hv

    def disCoRoute(self, t, src, dst):
        s = []
        Hh, Hv = self.minHopCount(src, dst, s)

        if self.satDescending(t, src) == self.satDescending(t, dst):
            route_s = [src]
            route_t = [dst]
            i = 0
            j = Hh
            for _ in range(Hh):
                reward_s = math.fabs(self.getPhi(t, s[i][0]) + self.getPhi(t, s[i + 1][0]))
                reward_t = math.fabs(self.getPhi(t, s[j][Hv]) + self.getPhi(t, s[j - 1][Hv]))
                if reward_s < reward_t:
                    route_t.insert(0, s[j - 1][Hv])
                    j = j - 1
                else:
                    route_s.append(s[i + 1][0])
                    i = i + 1
            assert(i == j)
            if Hv == 0:
                route_t = route_t[1:]
            else:
                route_s = route_s + [s[i][k] for k in range(1, Hv)]
            route = route_s + route_t
        else:
            route_s = [src]
            route_t = [dst]
            i = 0
            j = Hv
            for _ in range(Hv):
                reward_s = math.fabs(self.getPhi(t, s[0][i]) + self.getPhi(t, s[0][i + 1]))
                reward_t = math.fabs(self.getPhi(t, s[Hh][j]) + self.getPhi(t, s[Hh][j - 1]))
                if reward_s < reward_t:
                    route_s.append(s[0][i + 1])
                    i = i + 1
                else:
                    route_t.insert(0, s[Hh][j - 1])
                    j = j - 1
            assert(i == j)
            if Hh == 0:
                route_t = route_t[1:]
            else:
                route_s = route_s + [s[k][i] for k in range(1, Hh)]
            route = route_s + route_t

        render_info = []
        for i in range(len(route) - 1):
            render_info.append(
                {"endpoints": [route[i], route[i + 1]], "color": "red", "dashline": False}
            )
        return render_info

def convertConfig(config):
    res = {}
    for constellation in config["constellations"].keys():
        res[constellation] = {"scenarios": [], "numframes" : config["numframes"]}
        for scenario in config["scenarios"]:
            res[constellation]["scenarios"].append(' - '.join(scenario))
    return res


def generateScenario(request, config):
    constellation, scenario, frame = request
    satModel = SatelliteModel(config["constellations"][constellation])
    elapsedSeconds = frame
    scenarioExtension = {"nodes": [], "edges": []}
    for cityInfo in scenario.split('&'):
        print(cityInfo)
        userCities = cityInfo.split('-')
        userAcessPoints = []
        for _, userCity in enumerate(userCities):
            userCity = userCity.strip()
            userLocation = [math.radians(config["cities"][userCity][i])
                            for i in range(2)] + [0]
            userAP = satModel.queryNearest(
                userLocation, elapsedSeconds)
            userAcessPoints.append(userAP)
            '''
            scenarioExtension["nodes"].append({
                "name": "User_" + str(userIdx + 1),
                "coordinates": config["cities"][userCity] + [0],
                "color": "red"
            })
            scenarioExtension["edges"].append({
                "endpoints": [userIdx + satModel.size(), userAP],
                "color": "red",
                "dashline": False
            })
            '''
        scenarioExtension["edges"] += satModel.disCoRoute(elapsedSeconds,
            userAcessPoints[0], userAcessPoints[1])
    return scenarioExtension


def generateTopo(request, config):
    constellation, _, frame = request
    satModel = SatelliteModel(config["constellations"][constellation])
    elapsedSeconds = frame
    return satModel.genTopology(elapsedSeconds)


def generateFrame(request, config):
    topo = generateTopo(request, config)
    scenarioExtension = generateScenario(request, config)
    topo["nodes"] += scenarioExtension["nodes"]
    topo["edges"] += scenarioExtension["edges"]
    return topo


if __name__ == "__main__":
    tgconfig = json.load(open("tgconfig.json"))
    config = convertConfig(tgconfig)
    json.dump(config, open("config.json", 'w'))

    for constellation, scenarios in config.items():
        print("Generating constellation {}".format(constellation))
        path = "constellations/{}".format(constellation)
        if not os.path.exists(path):
            os.makedirs(path)
        commonNodes = []
        for t in range(tgconfig["numframes"]):
            commonNodes.append(generateTopo(
                [constellation, "", t], tgconfig)["nodes"])
        commonEdges = generateTopo([constellation, "", 0], tgconfig)["edges"]
        json.dump({
            "nodes": commonNodes,
            "edges": commonEdges
        }, open("{}/common.json".format(path), "w"))
        for scenario, numframes in scenarios.items():
            print("Generating scenario {}".format(scenario))
            frames = []
            for t in range(numframes):
                frames.append(generateScenario(
                    [constellation, scenario, t], tgconfig))
            json.dump(frames, open("{}/{}.json".format(path, scenario), "w"))
