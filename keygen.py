import hashlib
import time

SECRET = "RIO_SECRET"

def generate_key(key_type):
    if key_type == "LIFE":
        timestamp = 0
    else:
        timestamp = int(time.time() * 1000)

    raw = f"VIP-{key_type}-{timestamp}"
    sign = hashlib.md5((raw + SECRET).encode()).hexdigest()[:4]

    return f"{raw}-{sign}"