from flask import Flask, request
from time import time
app = Flask(__name__)

distances = dict()
goal = 0

@app.route("/")
def index():
    return str(distances)

@app.route("/", methods=["PUT"])
def update():
    ergs = request.form['ergs']
    data = request.form['data']
    now = time()
    for erg, val in zip(ergs, data):
        if erg not in distances:
            goal += val
        distances[erg] = val, now
