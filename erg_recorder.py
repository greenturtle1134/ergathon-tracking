import requests

SERVER = "https://ergathontracker.sites.tjhsst.edu/"


class Erg:

    def __init__(self, distance, name):
        self.distance = distance
        self.name = name


class Tracker:

    def __init__(self, node_id, node_name):
        self.ergs = list()
        self.node_id = node_id
        self.node_name = node_name

    def send_distances(self):
        data = list()
        for index, erg in enumerate(self.ergs):
            data.append({
                "distance": erg.distance,
                "name": erg.name,
                "node": self.node_id,
                "subnode": index,
            })
        return requests.put(SERVER + "ergs/", json=data)
