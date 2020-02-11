from flask import Flask, request, current_app, g, render_template
from flask.cli import with_appcontext
from time import time
import server_secret
import psycopg2

app = Flask(__name__)


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
    cur = get_db_cursor()
    cur.execute("SELECT * FROM ergs;")
    erg_matrix = cur.fetchall()
    erg_stats = {
        "sum": 0,
    }
    erg_list = list()
    for id, erg_serial, node, subnode, distance, last_update in erg_matrix:
        erg_stats["sum"] += distance
        erg_list.append({
            "serial": erg_serial,
            "node": node,
            "subnode": subnode,
            "distance": distance
        })
    erg_stats["percent"] = distance*100/1000000
    return render_template("index.html", erg_stats = erg_stats, erg_list = erg_list)


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
