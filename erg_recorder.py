import requests

SERVER = "https://ergathontracker.sites.tjhsst.edu/"

def send_distances(ergs):
    data = list()
    for erg in ergs:
        data.append({"name":erg, "distance":ergs[erg]})
    return requests.put(SERVER, json=data)
