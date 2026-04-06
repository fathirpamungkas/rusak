from flask import Flask, request, jsonify, render_template, redirect, session
import sqlite3, time, hashlib
import jwt

SECRET_KEY = "API_SECRET"
from flask import Flask, request, jsonify, render_template, redirect, session
from flask import Flask, request, jsonify
import sqlite3, time
import sqlite3
import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
import hashlib, time

SECRET = "RIO_SECRET"

def generate_key(type):
    if type == "LIFE":
        timestamp = 0
    else:
        timestamp = int(time.time()*1000)

    raw = f"VIP-{type}-{timestamp}"
    sign = hashlib.md5((raw+SECRET).encode()).hexdigest()[:4]

    return f"{raw}-{sign}"

app = Flask(__name__)
app.secret_key = "secret123"

api_limit = {}

@app.before_request
def limit():
    ip = request.remote_addr

    api_limit[ip] = api_limit.get(ip, 0) + 1

    if api_limit[ip] > 100:
        return "Rate limit!"

@app.route("/generate", methods=["POST"])
def generate():
    type = request.form.get("type")

    key = generate_key(type)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    now = int(time.time()*1000)

    duration = {
        "1D": 86400000,
        "7D": 7*86400000,
        "30D": 30*86400000,
        "LIFE": 0
    }

    expire = 0 if type=="LIFE" else now + duration[type]

    c.execute("INSERT INTO keys VALUES (?,?,?,?,?,?)",
              (key,"",type,now,expire,"ACTIVE"))

    conn.commit()

    return redirect("/dashboard")

def create_token(username):
    return jwt.encode({"user": username}, SECRET_KEY, algorithm="HS256")

login_attempts = {}

@app.route("/", methods=["GET","POST"])
def login():
    ip = request.remote_addr

    if login_attempts.get(ip, 0) > 5:
        return "Too many attempts"

    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")

        # hash input
        pw = hashlib.sha256(pw.encode()).hexdigest()

        conn = connect()
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pw))
        data = c.fetchone()

        if data:
            session["login"] = True
            login_attempts[ip] = 0
            return redirect("/dashboard")
        else:
            login_attempts[ip] = login_attempts.get(ip, 0) + 1

    return render_template("login.html")

@app.route("/user/<key>")
def user_panel(key):

    conn = connect()
    c = conn.cursor()

    c.execute("SELECT * FROM keys WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        return "Key tidak ditemukan"

    return f"""
    Key: {row[0]} <br>
    Device: {row[1]} <br>
    Type: {row[2]} <br>
    Expire: {row[4]} <br>
    Status: {row[5]}
    """

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json

    user = data.get("username")
    pw = data.get("password")

    conn = connect()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pw))
    row = c.fetchone()

    if row:
        token = create_token(user)
        return jsonify({"token": token})

    return jsonify({"error":"invalid"})

@app.route("/dashboard")
def dashboard():

    if not session.get("login"):
        return redirect("/")

    page = int(request.args.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page

    conn = connect()
    c = conn.cursor()

    c.execute("SELECT * FROM keys LIMIT ? OFFSET ?", (per_page, offset))
    c.execute("SELECT COUNT(*) FROM keys")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM keys WHERE status='ACTIVE'")
    active = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM keys WHERE status='BLACKLIST'")
    banned = c.fetchone()[0]
    keys = c.fetchall()

    return render_template("dashboard.html",
    keys=keys,
    total=total,
    active=active,
    banned=banned,
    page=page
)

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS keys (
        key TEXT PRIMARY KEY,
        device TEXT,
        type TEXT,
        created INTEGER,
        expire INTEGER,
        status TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS logs (
        action TEXT,
        time INTEGER
    )""")

    # hash password
    admin_pw = hashlib.sha256("12345".encode()).hexdigest()

    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', ?, 'admin')", (admin_pw,))

    conn.commit()
    conn.close()

def connect():
    return sqlite3.connect("database.db")

def log_action(action):
    conn = connect()
    c = conn.cursor()

    c.execute("INSERT INTO logs VALUES (?,?)", (action, int(time.time())))
    conn.commit()

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