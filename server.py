from flask import Flask, request, jsonify
import sqlite3, time

app = Flask(__name__)

def connect():
    return sqlite3.connect("database.db")

@app.route("/validate", methods=["POST"])
def validate():
    key = request.form.get("key")
    device = request.form.get("device")

    conn = connect()
    c = conn.cursor()

    c.execute("SELECT * FROM keys WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        return jsonify({"status":"invalid"})

    # blacklist
    if row[5] == "BLACKLIST":
        return jsonify({"status":"banned"})

    # expired
    now = int(time.time()*1000)
    if row[4] != 0 and row[4] < now:
        return jsonify({"status":"expired"})

    # bind device
    if row[1] == "":
        c.execute("UPDATE keys SET device=? WHERE key=?", (device, key))
        conn.commit()
        return jsonify({"status":"ok"})

    if row[1] != device:
        return jsonify({"status":"used"})

    return jsonify({"status":"ok"})