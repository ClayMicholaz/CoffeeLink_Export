import os

from flask import Flask, jsonify


app = Flask(__name__)


@app.route("/")
def health_root():
    return jsonify({
        "status": "ok",
        "message": "Vercel Python function is running",
    })


@app.route("/__health/env")
def health_env():
    database_url = os.environ.get("DATABASE_URL")
    secret_key = os.environ.get("SECRET_KEY")
    return jsonify({
        "status": "ok",
        "database_url_set": bool(database_url),
        "database_scheme": database_url.split(":", 1)[0] if database_url else None,
        "secret_key_set": bool(secret_key),
    })
