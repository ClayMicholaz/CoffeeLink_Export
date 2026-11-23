try:
    from app import app
except Exception as exc:
    from flask import Flask, jsonify

    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def application_error(path):
        return jsonify({
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }), 500
