from flask import Flask, request, current_app, g, render_template
from flask.cli import with_appcontext
from time import time
from datetime import *
import server_secret
import psycopg2

app = Flask(__name__)
start_time = datetime(2020, 2, 13, 4, 30)
goal = 1000000
in_progress = False


def get_db_cursor():
    if 'db_conn' not in g:
        g.db_conn = psycopg2.connect(user="site_ergathontracker", host="postgres1.csl.tjhsst.edu",
                                     database="site_ergathontracker", password=server_secret.sql_password)
    if 'db_cur' not in g:
        g.db_cur = g.db_conn.cursor()
    return g.db_cur


@app.teardown_appcontext
def on_teardown(error):
    db_cur = g.pop("db_cur", None)
    if db_cur is not None:
        db_cur.close()
    db_conn = g.pop("db_conn", None)
    if db_conn is not None:
        db_conn.commit()
        db_conn.close()


@app.route("/")
def index():
    return show_progress_screen()


def show_progress_screen():
    cur = get_db_cursor()
    cur.execute("SELECT * FROM ergs;")
    erg_matrix = cur.fetchall()
    total = 0
    count = 0
    erg_list = list()
    for erg_id, erg_serial, node, subnode, distance, last_update in erg_matrix:
        total += distance
        count += 1
        erg_list.append({
            "serial": erg_serial,
            "node": node,
            "subnode": subnode,
            "distance": distance
        })
    percent = total * 100 / goal
    elapsed = datetime.now() - start_time
    speed = total / elapsed.total_seconds()
    pace_delta = elapsed / (total / 500 / count)
    pace = str(pace_delta.seconds // 60) + ":" + str(pace_delta.seconds % 60)
    return render_template("index.html", sum=total, percent=percent, goal=goal,
                           time=time, speed=speed, pace=pace, elapsed=elapsed, erg_list=erg_list)


@app.route("/ergs/", methods=["PUT"])
def on_erg_update():
    cursor = get_db_cursor()
    count = 0
    total = 0
    for erg in request.get_json():
        count += 1
        total += erg["distance"]
        cursor.execute("INSERT INTO ergs (erg_serial, node, subnode, distance, last_update) "
                       "VALUES (%s, %s, %s, %s, NOW()) "
                       "ON CONFLICT ON CONSTRAINT unique_serial "
                       "DO UPDATE SET distance = EXCLUDED.distance, "
                       "erg_serial = EXCLUDED.erg_serial, "
                       "last_update = EXCLUDED.last_update,"
                       "node = EXCLUDED.node,"
                       "subnode = EXCLUDED.subnode",
                       (erg["serial"], erg["node"], erg["subnode"], erg["distance"]))
    return "{!s} ergs adding to {!s} meters".format(count, total)


@app.route("/nodes/", methods=["POST"])
def register_node():
    data = request.get_json()
    cursor = get_db_cursor()
    cursor.execute("INSERT INTO nodes (node_id, name) "
                   "VALUES (%s, %s) "
                   "ON CONFLICT ON CONSTRAINT unique_id "
                   "DO UPDATE SET name = EXCLUDED.name",
                   (data["id"], data["name"]))
    return "Name recorded."


@app.route("/nodes/<int:node_id>")
def query_node(node_id):
    cursor = get_db_cursor()
    cursor.execute("SELECT name FROM nodes WHERE node_id = %s;", (node_id,))
    result = cursor.fetchone()
    if result is not None:
        return result[0]
    else:
        return ""
