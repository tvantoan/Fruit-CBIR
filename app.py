"""Entry point for running the Flask application."""

import os
import sys
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from infrastructure.repositories import ImageRepository, FeatureRepository
from presentation.controllers import api_bp
from infrastructure.database.database import Database
from infrastructure.persistence.seed_data import SeedData
from usecases.feature_extractor import FeatureExtractor
from infrastructure.persistence.models import db

load_dotenv()
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
BACKEND_PORT = int(os.getenv('BACKEND_PORT', '5001'))
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

db.init_app(app)
migrate = Migrate(app, db, directory=os.path.join(PROJECT_ROOT, 'infrastructure', 'persistence', 'migrations'))
CORS(app, origins=FRONTEND_URL)
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    with app.app_context():
        Database.initialize()
        import sys
        if len(sys.argv) > 1 and sys.argv[1] in ['reset', 'clear']:
            from usecases.feature_extractor import FeatureExtractor
            from infrastructure.persistence.seed_data import SeedData

            print("Starting Seed Data process...")
            seed_service = SeedData(feature_extractor=FeatureExtractor())
            seed_service.execute()
            sys.exit(0)
    app.run(debug=True, port=BACKEND_PORT)