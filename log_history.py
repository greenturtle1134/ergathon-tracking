import psycopg2
import server_secret
from time import sleep


connection, cursor = None, None


def open_connection():
    global connection, cursor
    connection = psycopg2.connect(user="site_ergathontracker", host="postgres1.csl.tjhsst.edu",
                                     database="site_ergathontracker", password=server_secret.sql_password)
    cursor = connection.cursor()


def close_connection():
    cursor.close()
    connection.commit()
    connection.close()


def update():
    if cursor is not None:
        cursor.execute("INSERT INTO history (erg_serial, distance, time) SELECT erg_serial, distance, NOW() FROM ergs ORDER BY node, erg_serial")


def get_sum():
    total = 0
    if cursor is not None:
        cursor.execute("SELECT distance FROM ergs;")
        erg_matrix = cursor.fetchall()
        for result in erg_matrix:
            total += result[0]
    return total


if __name__ == "__main__":
    open_connection()
    sum = get_sum()
    close_connection()
    while True:
        open_connection()
        new_sum = get_sum()
        if new_sum != sum:
            sum = new_sum
            print("Updating.")
            update()
        close_connection()
        sleep(60)
