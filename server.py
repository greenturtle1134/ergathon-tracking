from flask import Flask, request
from time import time
app = Flask(__name__)


@app.route("/")
def index():
    return "Hello World"

@app.route("/", methods=["PUT"])
def update():
    count = 0
    sum = 0
    for erg in request.get_json():
        count += 1
        sum += erg["distance"]
        app.logger.info("Processed erg {} with distance {!s}".format(erg["name"], erg["distance"]))
    return "{!s} ergs adding to {!s} meters".format(count, sum)
