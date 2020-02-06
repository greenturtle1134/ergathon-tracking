import requests

SERVER = "https://ergathontracker.sites.tjhsst.edu/"

def send_distances(data):
    ergs = list()
    distances = list()
    for erg in data:
        ergs.append(erg)
        distances.append(data[erg])
    return requests.put(SERVER, {"ergs":ergs, "data":distances})

if __name__ == "__main__":
    response = send_distances({"A":50, "B":100})
    print(response.json())
