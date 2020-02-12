import datetime
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
        interface_path = os.path.dirname(os.path.abspath(__file__)) + "\\lib\\"
    path = interface_path + DLL_NAME  # Load DLL from lib folder
    DLL = WinDLL(path)
    print("Loaded interface DLL from {}".format(path))


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
        self.ergs = list()

    def discover_ergs(self):
        start_error = DLL.Init()  # Init the interface and count ergs
        if start_error != 0:
            log("Error on DLL startup: " + str(start_error))
        log("Initialized DLL.")
        erg_count = DLL.GetNumDevices2()
        self.ergs = list()
        DLL.GetSerialNumber.restype = c_char_p  # Declare a string return type
        serials = set()
        for port in range(erg_count):
            serial = DLL.GetSerialNumber(port).decode("utf-8")
            if serial in serials:
                log("ERROR: Repeated serial!")
            serials.add(serial)
            self.ergs.append(Erg(serial, port))
            log("Discovered erg {}".format(serial))
        log("Discovered {} erg(s)".format(erg_count))

    def update_ergs(self):
        for erg in self.ergs:
            erg.update()
        self.send_distances()

    def send_info(self):
        response = requests.post(SERVER + "nodes/", json={
            "name": self.node_name,
            "id": self.node_id
        })
        if response.status_code == 200:
            log("Updated server's node registry.")
        else:
            log(" ".join(("ERROR:", response.status_code, response.reason, "in sending node data.")))

    def send_distances(self):
        data = list()
        for index, erg in enumerate(self.ergs):
            data.append({
                "distance": erg.distance,
                "serial": erg.serial,
                "node": self.node_id,
                "subnode": erg.port,
            })
        response = requests.put(SERVER + "ergs/", json=data)
        if response.status_code != 200:
            log(" ".join(("ERROR:", response.status_code, response.reason, "in sending erg data.")))

    def __str__(self):
        return "Tracker {} ({}) with ergs {}" .format(self.node_name, self.node_id, self.erg_string())

    def erg_string(self):
        return ", ".join(("{} ({}m)".format(erg.serial, erg.distance) for erg in self.ergs))


def get_node_name(node_id):
    response = requests.get(SERVER + "nodes/" + str(node_id))
    if response.status_code == 200 and len(response.text) > 0:
        return response.text
    else:
        return None


def log(string):
    print("[{}]:".format(str(datetime.datetime.now())), string)


def main():
    load_dll(input("Enter interface directory (blank for \\lib): "))
    tracker_id = int(input("(IMPORTANT) Enter tracker ID: "))
    old_name = get_node_name(tracker_id)
    if old_name is None:
        old_name = str(tracker_id)
        name = input("Enter tracker name (blank to use id): ".format(old_name))
    else:
        print("Name found on server:", old_name)
        name = input("Enter tracker name (blank to continue using \"{}\"): ".format(old_name))
    if len(name) == 0:
        name = old_name
    tracker = Tracker(tracker_id, name)
    tracker.send_info()
    log_period = 60
    period_input = input("Enter approx. log period (blank to continue using {}s): ".format(str(log_period)))
    if len(period_input) > 0:
        log_period = int(period_input)

    refresh_period = 1200
    period_input = input("Enter approx. re-discover period (blank to continue using {}s): ".format(str(refresh_period)))
    if len(period_input) > 0:
        refresh_period = int(period_input)
    print("================\n")
    input("Ready to discover ergs! (Enter to continue)")
    tracker.discover_ergs()
    input("Proceed? (Enter to continue)")
    print()
    count = 0
    while True:
        sleep(0.8)
        count += 1
        tracker.update_ergs()
        if count % log_period == 0:
            log(tracker.erg_string())
        if count % refresh_period == 0:
            log("Refreshing ergs.")
            tracker.discover_ergs()


if __name__ == "__main__":
    main()
