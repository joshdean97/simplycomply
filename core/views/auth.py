from flask import Blueprint, render_template, request, url_for, flash, redirect
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from ..models import User
from ..extensions import db
from ..functions import check_password_strength

from datetime import datetime

# auth blueprint
auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/login/", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email").lower().strip()
        password = request.form.get("password")

        # Query user by email
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email does not exist.", "error")
        else:
            # Log in the user
            if check_password_hash(user.password_hash, password):
                login_user(user, remember=True)
                flash(f"Welcome back, {user.name}!", "success")
                if user.subscription_plan == None:
                    return redirect(url_for("views.choose_plan", user_id=user.id))
                else:
                    return redirect(
                        url_for("views.dashboard")
                    )  # Redirect to a protected page (adjust URL as needed)
            else:
                flash("Incorrect password.", "error")

    current_user.last_login = datetime.now()
    db.session.commit()

    context = {"current_user": current_user}

    return render_template("login.html", **context)


@auth.route("/register/", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validate inputs
        if len(first_name) < 2:
            flash("First name must be at least 2 characters.", "error")
        elif len(last_name) < 2:
            flash("Last name must be at least 2 characters.", "error")
        elif not email:
            flash("Email is required.", "error")
        elif User.query.filter_by(email=email).first():
            flash("Email already exists.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif not check_password_strength(password):
            flash(
                "Password is too weak. It must be at least 8 characters long and include uppercase letters, lowercase letters, numbers, and special characters.",
                "error",
            )
        else:
            # Add new user to the database
            hashed_password = generate_password_hash(password)
            new_user = User(
                name=f"{first_name.title().strip()} {last_name.title().strip()}",
                email=email.lower().strip(),
                password_hash=hashed_password,
                role="admin",  # Default to 'admin' role;
                manager_id=None,
            )
            db.session.add(new_user)
            db.session.commit()

            flash("Account created successfully! You can now log in.", "success")
            return redirect(url_for("auth.login"))
    context = {}

    return render_template("register.html", **context)


@auth.route("/logout/")
@login_required
def logout():
    user = current_user

    logout_user()
    flash(f"Logged out!", "success")
    return redirect(url_for("auth.login"))
