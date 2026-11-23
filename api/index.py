try:
    from app import app as flask_app
except Exception as exc:
    from flask import Flask, jsonify

    flask_app = Flask(__name__)

    @flask_app.route("/", defaults={"path": ""})
    @flask_app.route("/<path:path>")
    def startup_error(path):
        return jsonify({
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }), 500


app = flask_app
