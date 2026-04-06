from flask import Flask, request, jsonify, render_template, redirect, session
import sqlite3, time, hashlib, os
import jwt

app = Flask(__name__)
app.secret_key = "secret123"

SECRET = "RIO_SECRET"
SECRET_KEY = "API_SECRET"

# =========================
# DATABASE
# =========================
def connect():
    return sqlite3.connect("database.db")

def init_db():
    conn = connect()
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

    admin_pw = hashlib.sha256("Fathir18".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', ?, 'admin')", (admin_pw,))

    conn.commit()
    conn.close()

# =========================
# SECURITY
# =========================
api_limit = {}
login_attempts = {}

@app.before_request
def security():
    ip = request.remote_addr

    # rate limit
    api_limit[ip] = api_limit.get(ip, 0) + 1
    if api_limit[ip] > 100:
        return "Rate limit!"

    # auto init db
    init_db()

# =========================
# UTIL
# =========================
def generate_key(type):
    timestamp = 0 if type == "LIFE" else int(time.time()*1000)
    raw = f"VIP-{type}-{timestamp}"
    sign = hashlib.md5((raw+SECRET).encode()).hexdigest()[:4]
    return f"{raw}-{sign}"

def create_token(username):
    return jwt.encode({"user": username}, SECRET_KEY, algorithm="HS256")

def log_action(action):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO logs VALUES (?,?)", (action, int(time.time())))
    conn.commit()

# =========================
# ROUTES
# =========================
@app.route("/test")
def test():
    return "Server OK"

@app.route("/", methods=["GET","POST"])
def login():
    ip = request.remote_addr

    if login_attempts.get(ip, 0) > 5:
        return "Too many attempts"

    if request.method == "POST":
        user = request.form.get("username")
        pw = hashlib.sha256(request.form.get("password").encode()).hexdigest()

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
    keys = c.fetchall()

    c.execute("SELECT COUNT(*) FROM keys")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM keys WHERE status='ACTIVE'")
    active = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM keys WHERE status='BLACKLIST'")
    banned = c.fetchone()[0]

    return render_template("dashboard.html",
        keys=keys,
        total=total,
        active=active,
        banned=banned,
        page=page
    )

@app.route("/generate", methods=["POST"])
def generate():
    type = request.form.get("type")
    key = generate_key(type)

    conn = connect()
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
    log_action("Generate " + key)

    return redirect("/dashboard")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    user = data.get("username")
    pw = hashlib.sha256(data.get("password").encode()).hexdigest()

    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pw))
    row = c.fetchone()

    if row:
        return jsonify({"token": create_token(user)})

    return jsonify({"error":"invalid"})

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
    if row[5] == "BLACKLIST":
        return jsonify({"status":"banned"})

    now = int(time.time()*1000)
    if row[4] != 0 and row[4] < now:
        return jsonify({"status":"expired"})

    if row[1] == "":
        c.execute("UPDATE keys SET device=? WHERE key=?", (device, key))
        conn.commit()
        return jsonify({"status":"ok"})

    if row[1] != device:
        return jsonify({"status":"used"})

    return jsonify({"status":"ok"})

# =========================
# RUN
# =========================
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))