import os
import uuid
import time
from flask import Flask, request, jsonify, render_template
from db import get_conn

app = Flask(__name__)

TEST_MODE = os.environ.get("TEST_MODE") == "1"


def now_ms():
    if TEST_MODE:
        header = request.headers.get("x-test-now-ms")
        if header:
            return int(header)
    return int(time.time() * 1000)


def is_expired(row):
    if row["expires_at"] is not None and now_ms() >= row["expires_at"]:
        return True
    if row["max_views"] is not None and row["view_count"] >= row["max_views"]:
        return True
    return False


@app.route("/api/healthz")
def healthz():
    try:
        conn = get_conn()
        conn.close()
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"ok": False}), 500


@app.route("/api/pastes", methods=["POST"])
def create_paste():
    data = request.get_json()

    if not data or not data.get("content") or not isinstance(data["content"], str):
        return jsonify({"error": "Invalid content"}), 400

    ttl = data.get("ttl_seconds")
    max_views = data.get("max_views")

    if ttl is not None and (not isinstance(ttl, int) or ttl < 1):
        return jsonify({"error": "Invalid ttl_seconds"}), 400

    if max_views is not None and (not isinstance(max_views, int) or max_views < 1):
        return jsonify({"error": "Invalid max_views"}), 400

    paste_id = str(uuid.uuid4())
    created_at = now_ms()
    expires_at = created_at + ttl * 1000 if ttl else None

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO pastes (id, content, created_at, expires_at, max_views)
        VALUES (%s, %s, %s, %s, %s)
    """, (paste_id, data["content"], created_at, expires_at, max_views))

    conn.commit()
    cur.close()
    conn.close()

    base_url = request.host_url.rstrip("/")

    return jsonify({
        "id": paste_id,
        "url": f"{base_url}/p/{paste_id}"
    })


@app.route("/api/pastes/<paste_id>")
def fetch_paste_api(paste_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM pastes WHERE id=%s", (paste_id,))
    row = cur.fetchone()

    if not row:
        return jsonify({"error": "Not found"}), 404

    columns = [desc[0] for desc in cur.description]
    paste = dict(zip(columns, row))

    if is_expired(paste):
        return jsonify({"error": "Not found"}), 404

    cur.execute("""
        UPDATE pastes SET view_count = view_count + 1 WHERE id=%s
    """, (paste_id,))
    conn.commit()

    remaining_views = (
        None if paste["max_views"] is None
        else max(paste["max_views"] - (paste["view_count"] + 1), 0)
    )

    response = {
        "content": paste["content"],
        "remaining_views": remaining_views,
        "expires_at": (
            time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(paste["expires_at"] / 1000))
            if paste["expires_at"] else None
        )
    }

    cur.close()
    conn.close()
    return jsonify(response)


@app.route("/p/<paste_id>")
def view_paste(paste_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM pastes WHERE id=%s", (paste_id,))
    row = cur.fetchone()

    if not row:
        return render_template("error.html"), 404

    columns = [desc[0] for desc in cur.description]
    paste = dict(zip(columns, row))

    if is_expired(paste):
        return render_template("error.html"), 404

    cur.execute("""
        UPDATE pastes SET view_count = view_count + 1 WHERE id=%s
    """, (paste_id,))
    conn.commit()

    cur.close()
    conn.close()
    return render_template("view_paste.html", content=paste["content"])


@app.route("/")
def index():
    return render_template("index.html")
