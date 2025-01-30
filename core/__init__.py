# flask imports
from flask import Flask, request, redirect, url_for, render_template, flash, session, g
from flask_login import LoginManager, login_required, current_user

import stripe

# filesystem imports
from dotenv import load_dotenv, find_dotenv
from os import path
import os

from .extensions import migrate, db
from .models import User, Restaurant, Document, Template, UserRestaurant
from .functions import send_email

# find .env in filesystem
dotenv_path = find_dotenv()
# Load environment variables from.env file
load_dotenv()

# constants
DB_NAME = "database.db"

# ---------------------------------------------------------------------------- #
#                               factory function                               #
# ---------------------------------------------------------------------------- #


def create_app(phase):
    app = Flask(__name__)

    # app configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    if phase == "development":
        db_uri = os.environ.get("DB_URI_DEV")
    elif phase == "production":
        db_uri = os.environ.get("DB_URI_PROD")
    if not db_uri:
        raise ValueError("No DB_URI environment variable set")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_POOL_RECYCLE"] = 3600
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if phase == "production":
        app.config["STRIPE_PUBLIC_KEY"] = os.environ.get("STRIPE_TEST_PUBLIC")
        app.config["STRIPE_SECRET_KEY"] = os.environ.get("STRIPE_TEST_SECRET")

    if phase == "development":
        app.config["STRIPE_PUBLIC_KEY"] = os.environ.get("STRIPE_PUBLIC_KEY")
        app.config["STRIPE_SECRET_KEY"] = os.environ.get("STRIPE_SECRET_KEY")

    stripe.api_key = app.config["STRIPE_SECRET_KEY"]

    # Initialize database
    db.init_app(app)
    migrate.init_app(app, db)

    # Import routes
    from .views.views import views
    from .views.auth import auth
    from .views.admin import admin
    from .views.create import create
    from .views.stripe import payments

    # Register routes
    app.register_blueprint(views)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(create)
    app.register_blueprint(payments)

    # contact form post route
    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            # Handle form submission
            name = request.form.get("name")
            email = request.form.get("email")
            subject = request.form.get("subject")
            message = request.form.get("message")

            # add email logic

            return redirect(url_for("views.index"))

        # Render the contact form for GET requests
        return render_template("contact.html")

    @app.route("/thank-you")
    def thank_you():
        return "Thank you for your message!"

    @app.before_request
    def ensure_default_restaurant():
        # Ensure user is authenticated
        if current_user.is_authenticated:
            # Check if a restaurant is already in session
            if "selected_restaurant_id" not in session:
                # Set default to the first restaurant in user's list
                if current_user.restaurants:
                    session["selected_restaurant_id"] = current_user.restaurants[0].id
                    g.selected_restaurant = current_user.restaurants[0]
                else:
                    g.selected_restaurant = None  # No restaurants available
            else:
                # Fetch the selected restaurant for use in the request context
                g.selected_restaurant = next(
                    (
                        r
                        for r in current_user.restaurants
                        if r.id == session["selected_restaurant_id"]
                    ),
                    None,
                )

    @app.route("/select-restaurant", methods=["POST"])
    @login_required
    def select_restaurant():
        selected_restaurant_id = request.form.get("restaurant_id")
        if selected_restaurant_id:
            # Validate the restaurant ID belongs to the current user
            if any(
                r.id == int(selected_restaurant_id) for r in current_user.restaurants
            ):
                session["selected_restaurant_id"] = int(selected_restaurant_id)
                flash("Restaurant selection updated.", "success")
            else:
                flash("Invalid restaurant selected.", "danger")
        return redirect(request.referrer or url_for("views.dashboard"))

    @app.route("/test-email")
    def test_email():
        send_email()

        return "sent"

    # Error handling
    @app.errorhandler(404)
    def not_found(e):
        return "404 Not Found", 404

    @app.errorhandler(500)
    def server_error(e):
        return "500 Server Error", 500

    from datetime import datetime

    @app.context_processor
    def inject_year():
        return {"current_year": datetime.now().year}

    # login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    login_manager.login_message = "Please log in to access this page."

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
