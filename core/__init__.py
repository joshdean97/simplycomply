# flask imports
from flask import Flask
from flask_login import LoginManager

# filesystem imports
from dotenv import load_dotenv, find_dotenv
from os import path
import os

from .extensions import migrate, db
from .models import User, Restaurant, UserRestaurant

# find .env in filesystem
find_dotenv()
# Load environment variables from.env file
load_dotenv()

# constants
DB_NAME = 'database.db'

def create_app():
    app = Flask(__name__)
    
    # app configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    migrate.init_app(app, db)
    
    
    # Import routes
    from .views import views
    from .auth import auth
    
    # Register routes
    app.register_blueprint(views)
    app.register_blueprint(auth)
    
    # Error handling
    @app.errorhandler(404)
    def not_found(e):
        return "404 Not Found", 404
    
    @app.errorhandler(500)
    def server_error(e):
        return "500 Server Error", 500
    
    # create database if one doesn't exist
    create_database(app)
    
        # login manager 
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.login_message = "Please log in to access this page."

    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    


    return app

def create_database(app):
    if not path.exists('core/database.db'):
        with app.app_context():
            db.create_all()
        print("Database created successfully")
