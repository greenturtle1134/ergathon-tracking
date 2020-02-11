import os
from time import sleep

import requests
from ctypes import *

SERVER = "https://ergathontracker.sites.tjhsst.edu/"
DLL_NAME = "erg.dll"
DLL = None


def load_dll(interface_path=""):
    global DLL
    if len(interface_path) == 0:
        interface_path = os.path.dirname(os.path.abspath(__file__))
    DLL = WinDLL(interface_path + "\\" + DLL_NAME)  # Load DLL from same folder
    print("Loaded interface DLL from {}".format(interface_path + "\\" + DLL_NAME))
    start_error = DLL.Init()  # Init the interface and count ergs
    if start_error != 0:
        print("Error on DLL startup:", start_error)
    print("Initialized DLL.")


class Erg:

    def __init__(self, serial, port):
        self.serial = serial
        self.port = port
        self.distance = 0

    def update(self):
        self.distance = DLL.GetDistance(self.port)
        return self.distance


class Tracker:

    def __init__(self, node_id, node_name=None):

        self.node_id = node_id
        if node_name is None or len(node_name) == 0:
            self.node_name = str(node_id)  # If no node name is given, default to the ID
        else:
            self.node_name = node_name

        erg_count = DLL.GetNumDevices()

        self.ergs = list()
        DLL.GetSerialNumber.restype = c_char_p  # Declare a string return type
        for port in range(erg_count):
            serial = DLL.GetSerialNumber(port).decode("utf-8")
            self.ergs.append(Erg(serial, port))
            print("Discovered erg {}".format(serial))
        print("Discovered {} erg(s)".format(erg_count))

    def update_ergs(self):
        for erg in self.ergs:
            x = erg.update()
            print(x)
        self.send_distances()

    def send_info(self):
        return requests.post(SERVER + "nodes/", json={
            "name": self.node_name,
            "id": self.node_id
        })

    def send_distances(self):
        data = list()
        for index, erg in enumerate(self.ergs):
            data.append({
                "distance": erg.distance,
                "serial": erg.serial,
                "node": self.node_id,
                "subnode": erg.port,
            })
        return requests.put(SERVER + "ergs/", json=data)


def main():
    load_dll(input("Enter interface directory (blank for this one): "))
    tracker = Tracker(int(input("Enter tracker ID: ")), input("Enter tracker name (blank to use ID): "))
    # tracker.send_info()
    while True:
        sleep(1)
        tracker.update_ergs()


if __name__ == "__main__":
    main()
