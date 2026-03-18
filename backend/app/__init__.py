import os
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__, static_folder='../static')

    app.config.from_object('app.config.Config')

    CORS(app, origins=["http://localhost:5173", "http://localhost:5001"])

    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app
