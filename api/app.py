import sqlite3
from flask import Flask, jsonify, request
from datetime import datetime
import random

app = Flask(__name__)
DB_PATH = "data/audience.db"

# ------------------------------
#  Fonction utilitaire SQL
# ------------------------------
def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    data = cur.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data

# ------------------------------
#  Initialisation DB
# ------------------------------
def init_db():
    run_query("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT UNIQUE,
        type TEXT,
        user TEXT
    )
    """)

    run_query("""
    CREATE TABLE IF NOT EXISTS audience_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        ts TEXT,
        screen_time REAL,
        volume INTEGER
    )
    """)

init_db()

# ------------------------------
#  STATUS (nécessaire pour tests)
# ------------------------------
@app.route("/status", methods=["GET"])
def status():
    return jsonify({"api": "running"}), 200

# ------------------------------
#  GET DATA (simulate device)
# ------------------------------
@app.route("/device/data/<device_id>", methods=["GET"])
def get_device_data(device_id):
    device = run_query("SELECT * FROM devices WHERE device_id=?", (device_id,), fetch=True)
    if not device:
        return jsonify({"error": "Device not found"}), 404

    sample = {
        "device_id": device_id,
        "ts": datetime.utcnow().isoformat(),
        "screen_time": round(random.uniform(1, 60), 2),
        "volume": random.randint(0, 100)
    }

    run_query("""
        INSERT INTO audience_data (device_id, ts, screen_time, volume)
        VALUES (?, ?, ?, ?)
    """, (device_id, sample["ts"], sample["screen_time"], sample["volume"]))

    return jsonify(sample), 200

# ------------------------------
#  POST DEVICE (testé par pytest)
# ------------------------------
@app.route("/device/add", methods=["POST"])
def add_device():
    data = request.get_json()
    if not data or "device_id" not in data:
        return jsonify({"error": "Missing device_id"}), 400

    try:
        run_query("""
            INSERT INTO devices (device_id, type, user)
            VALUES (?, ?, ?)
        """, (data["device_id"], data.get("type", "unknown"), data.get("user", "anonymous")))

        return jsonify({"message": "Device ajouté avec succès"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Device déjà existant"}), 409

# ------------------------------
#  POST AUDIENCE (pour pytest)
# ------------------------------
@app.route("/audience/add", methods=["POST"])
def add_audience():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing body"}), 400

    required = ["device_id", "screen_time", "volume"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    ts = data.get("ts", datetime.utcnow().isoformat())

    run_query("""
        INSERT INTO audience_data (device_id, ts, screen_time, volume)
        VALUES (?, ?, ?, ?)
    """, (data["device_id"], ts, data["screen_time"], data["volume"]))

    return jsonify({"message": "Audience entry added"}), 201

# ------------------------------
#  DELETE DEVICE
# ------------------------------
@app.route("/device/delete/<device_id>", methods=["DELETE"])
def delete_device(device_id):
    run_query("DELETE FROM devices WHERE device_id=?", (device_id,))
    return jsonify({"message": f"Device {device_id} supprimé"}), 200

# ------------------------------
#  LIST DEVICES
# ------------------------------
@app.route("/devices", methods=["GET"])
def list_devices():
    data = run_query("SELECT device_id, type, user FROM devices", fetch=True)
    devices = [{"device_id": d[0], "type": d[1], "user": d[2]} for d in data]
    return jsonify(devices), 200

# ------------------------------
#  LIST AUDIENCE ENTRIES
# ------------------------------
@app.route("/audience", methods=["GET"])
def list_audience():
    data = run_query("""
        SELECT device_id, ts, screen_time, volume
        FROM audience_data
        ORDER BY id DESC
        LIMIT 50
    """, fetch=True)

    measures = [
        {"device_id": d[0], "ts": d[1], "screen_time": d[2], "volume": d[3]}
        for d in data
    ]

    return jsonify(measures), 200

# ------------------------------
#  RUN SERVER
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
