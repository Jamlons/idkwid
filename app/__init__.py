from flask import Flask
from app.db import db
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config.from_object(Config)
app.secret_key = 'supersecretkey'

migrate = Migrate(app, db)

db.init_app(app)

# Import your routes and models after the app is initialized
from app import routes, models
