import datetime
import os
from time import sleep

import requests
from ctypes import *

DISTANCE_MAX = 40000

SERVER = "https://ergathontracker.sites.tjhsst.edu/"
DLL_NAME = "erg.dll"
DLL = None

LOG_PERIOD = 5
REFRESH_PERIOD = 60


def load_dll():
    global DLL
    path = os.path.dirname(os.path.abspath(__file__)) + "\\lib\\" + DLL_NAME  # Load DLL from lib folder
    DLL = WinDLL(path)
    print("Loaded interface DLL from {}".format(path))


class Erg:

    def __init__(self, serial, subnode):
        self.serial = serial
        self.subnode = subnode
        self.distance = 0


class Tracker:

    def __init__(self, node_id, node_name=None):
        self.node_id = node_id
        self.node_name = node_name
        self.ergs = dict()
        self.erg_count = 0

    def discover_ergs(self):
        start_error = DLL.Init()  # Init the interface and count ergs
        if start_error != 0:
            log("Error on DLL startup: " + str(start_error))
        log("Initialized DLL.")
        self.ergs = dict()
        DLL.GetSerialNumber.restype = c_char_p  # Declare a string return type
        serials = set()
        self.erg_count = DLL.GetNumDevices2()
        for port in range(self.erg_count):
            serial = DLL.GetSerialNumber(port).decode("utf-8")
            if serial in serials:
                log("ERROR: Repeated serial!")
            serials.add(serial)
            if serial not in self.ergs:
                self.ergs[serial] = Erg(serial, len(self.ergs))
            log("Discovered erg {}".format(serial))
        log("Discovered {} erg(s)".format(self.erg_count))

    def do_update(self):
        if not self.update_ergs():
            log("Update error. Refreshing ergs.")
            self.discover_ergs()
            log("Retrying update.")
            if not self.update_ergs():
                log("Error remains.")
        self.send_distances()

    def update_ergs(self):
        anomaly = False
        seen = set()
        for port in range(self.erg_count):
            serial = DLL.GetSerialNumber(port)
            if serial is None:
                anomaly = True
            else:
                serial = serial.decode("utf-8")
                distance = DLL.GetDistance(port)
                if serial in self.ergs:
                    self.ergs[serial].distance = distance
                else:
                    anomaly = True
                if distance < 0 or distance > DISTANCE_MAX:
                    anomaly = True
                if serial in seen:
                    anomaly = True
                seen.add(serial)
        return not anomaly

    def send_info(self):
        response = requests.post(SERVER + "nodes/", json={
            "name": self.node_name,
            "id": self.node_id
        })
        if response.status_code == 200:
            log("Updated server's node registry.")
            return True
        else:
            log(" ".join(("ERROR:", str(response.status_code), str(response.reason), "in sending node data.")))
            return False

    def send_distances(self):
        data = list()
        for serial in self.ergs:
            erg = self.ergs[serial]
            data.append({
                "distance": erg.distance,
                "serial": erg.serial,
                "node": self.node_id,
                "subnode": erg.subnode,
            })
        response = requests.put(SERVER + "ergs/", json=data)
        if response.status_code != 200:
            log(" ".join(("ERROR:", str(response.status_code), str(response.reason), "in sending erg data.")))

    def __str__(self):
        return "Tracker {} ({}) with ergs {}".format(self.node_name, self.node_id, self.erg_string())

    def erg_string(self):
        return ", ".join(("{} ({}m)".format(self.ergs[erg].serial, self.ergs[erg].distance) for erg in self.ergs))


def get_node_name(node_id):
    response = requests.get(SERVER + "nodes/" + str(node_id))
    if response.status_code == 200 and len(response.text) > 0:
        return response.text
    else:
        return None


def log(string):
    print("[{}]:".format(str(datetime.datetime.now())), string)


def main():
    load_dll()
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
    print("================\n")
    input("Ready to discover ergs! (Enter to continue)")
    tracker.discover_ergs()
    input("Proceed? (Enter to continue)")
    print()
    count = 0
    while True:
        sleep(0.8)
        count += 1
        tracker.do_update()
        if count % LOG_PERIOD == 0:
            log(tracker.erg_string())
        if count % REFRESH_PERIOD == 0:
            log("Refreshing ergs.")
            tracker.discover_ergs()


if __name__ == "__main__":
    main()
