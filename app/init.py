from flask import Flask
from .config import Config
from .db import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    from .main import bp as main_bp
    app.register_blueprint(main_bp)
    return app