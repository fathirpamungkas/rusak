import sqlite3
import time

def delete_expired():
    import time
    now = int(time.time() * 1000)

    conn = connect()
    c = conn.cursor()

    c.execute("DELETE FROM keys WHERE expire != 0 AND expire < ?", (now,))
    conn.commit()
    conn.close()


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

    conn.commit()
    conn.close()

def save_key(key, key_type, duration):
    now = int(time.time() * 1000)

    expire = 0 if key_type == "LIFE" else now + duration

    conn = connect()
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO keys VALUES (?, ?, ?, ?, ?, ?)",
              (key, "", key_type, now, expire, "ACTIVE"))

    conn.commit()
    conn.close()

def get_all_keys():
    conn = connect()
    c = conn.cursor()

    c.execute("SELECT * FROM keys")
    data = c.fetchall()

    conn.close()
    return data

def delete_key(key):
    conn = connect()
    c = conn.cursor()

    c.execute("DELETE FROM keys WHERE key=?", (key,))
    conn.commit()
    conn.close()

def blacklist_key(key):
    conn = connect()
    c = conn.cursor()

    c.execute("UPDATE keys SET status='BLACKLIST' WHERE key=?", (key,))
    conn.commit()
    conn.close()

def bind_device(key, device):
    conn = connect()
    c = conn.cursor()

    c.execute("SELECT device FROM keys WHERE key=?", (key,))
    data = c.fetchone()

    if data and data[0] == "":
        c.execute("UPDATE keys SET device=? WHERE key=?", (device, key))
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False