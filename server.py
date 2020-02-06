from flask import Flask, request
from time import time
app = Flask(__name__)


@app.route("/")
def index():
    return "Hello World

@app.route("/", methods=["PUT"])
def update():
    ergs = request.form['ergs']
    data = request.form['data']
    now = time()
    for erg, val in zip(ergs, data):
        # if erg not in distances:
            # goal += val
        # distances[erg] = val, now
        print(erg, val)
