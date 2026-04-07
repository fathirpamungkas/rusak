from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM keys")
    data = c.fetchall()

    return str(data)