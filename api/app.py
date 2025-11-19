import sqlite3
from flask import Flask, jsonify, request
from datetime import datetime
import os

app = Flask(__name__)

DB_PATH = "data/audience.db"


# -----------------------------------------------------
#  DB RESET POUR TESTS (évite erreurs 409)
# -----------------------------------------------------
def reset_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


# -----------------------------------------------------
#  SQL helper
# -----------------------------------------------------
def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    data = cur.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data


# -----------------------------------------------------
#  DB init
# -----------------------------------------------------
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


# RESET DB pour éviter les doublons en test local (pytest)
reset_db()
init_db()


# -----------------------------------------------------
#  Status
# -----------------------------------------------------
@app.route("/status", methods=["GET"])
def status():
    return jsonify({"api": "running"}), 200


# -----------------------------------------------------
#  DEVICE ADD (strict)
# -----------------------------------------------------
@app.route("/device/add", methods=["POST"])
def add_device():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing body"}), 400

    try:
        # device_id obligatoire + non vide
        if "device_id" not in data:
            return jsonify({"error": "Missing device_id"}), 400

        if not isinstance(data["device_id"], str) or data["device_id"].strip() == "":
            raise ValueError("Invalid device_id")

        # type obligatoire + non vide
        if "type" not in data or not isinstance(data["type"], str) or data["type"].strip() == "":
            raise ValueError("Invalid type")

        # user obligatoire + non vide
        if "user" not in data or not isinstance(data["user"], str) or data["user"].strip() == "":
            raise ValueError("Invalid user")

    except Exception:
        return jsonify({"error": "Invalid device data"}), 422

    # Insertion
    try:
        run_query("INSERT INTO devices (device_id, type, user) VALUES (?, ?, ?)",
                  (data["device_id"], data["type"], data["user"]))
        return jsonify({"message": "Device ajouté"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Device déjà existant"}), 409


# -----------------------------------------------------
#  AUDIENCE ADD
# -----------------------------------------------------
@app.route("/audience/add", methods=["POST"])
def add_audience():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing body"}), 400

    # ts peut être manquant → on le génère
    if "ts" not in data:
        data["ts"] = datetime.utcnow().isoformat()

    try:
        # device_id obligatoire + non vide
        if "device_id" not in data or not isinstance(data["device_id"], str) or data["device_id"].strip() == "":
            raise ValueError("Invalid device_id")

        # screen_time : nombre + >= 0
        if "screen_time" not in data or not isinstance(data["screen_time"], (int, float)) or data["screen_time"] < 0:
            raise ValueError("Invalid screen_time")

        # volume entre 0 et 100
        if "volume" not in data or not isinstance(data["volume"], int) or not (0 <= data["volume"] <= 100):
            raise ValueError("Invalid volume")

        # ts ISO
        datetime.fromisoformat(data["ts"])

    except Exception:
        return jsonify({"error": "Invalid data format"}), 422

    # Insertion
    run_query("""
        INSERT INTO audience_data (device_id, ts, screen_time, volume)
        VALUES (?, ?, ?, ?)
    """, (data["device_id"], data["ts"], data["screen_time"], data["volume"]))

    return jsonify({"message": "Audience added"}), 201


# -----------------------------------------------------
#  DEVICES LIST
# -----------------------------------------------------
@app.route("/devices", methods=["GET"])
def list_devices():
    data = run_query("SELECT device_id, type, user FROM devices", fetch=True)
    devices = [{"device_id": d[0], "type": d[1], "user": d[2]} for d in data]
    return jsonify(devices), 200


# -----------------------------------------------------
#  AUDIENCE LIST
# -----------------------------------------------------
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


# -----------------------------------------------------
# RUN SERVER
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
