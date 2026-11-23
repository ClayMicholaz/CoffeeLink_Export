"""Production entrypoint for CoffeeLink.

The marketplace implementation lives in app_new while this module keeps the
existing ``gunicorn app:app`` and ``python app.py`` commands stable.
"""

from app_new import app, initialize_database


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
