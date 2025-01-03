from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from werkzeug.security import generate_password_hash

from ..extensions import db
from ..models import User, Restaurant
from ..functions import admin_required

# Blueprint initialization
admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/panel/", methods=["GET", "POST"])
@login_required
@admin_required
def admin_dashboard():
    context = {
        "current_user": current_user,
        "managed_users": User.query.filter(User.manager_id == current_user.id),
    }
    return render_template("admin/admin_panel.html", **context)


# ---------------------------------------------------------------------------- #
#                            Route to add a new user                           #
# ---------------------------------------------------------------------------- #


@admin.route("/add-user/", methods=["GET", "POST"])
@login_required
@admin_required
def add_user():
    if request.method == "POST":
        name = request.form.get("name").title().strip()
        email = request.form.get("email").lower().strip()
        password = request.form.get("password")
        role = request.form.get("role")
        restaurant = request.form.get("restaurant")

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User with this email already exists.", "danger")
            return redirect(url_for("admin.add_user"))

        else:
            new_user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
                manager_id=current_user.id,
                restaurant_id=restaurant,
            )

        db.session.add(new_user)
        db.session.commit()
        flash("User added successfully!", "success")
        return redirect(url_for("admin.admin_dashboard"))

    # Pass all admins for selection
    admins = User.query.filter_by(role="admin").all()
    return render_template("admin/add_user.html", admins=admins)


# edit user


@admin.route("/edit-user/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        name = request.form.get("name").title().strip()
        email = request.form.get("email").lower().strip()
        role = request.form.get("role")
        restaurant = request.form.get("restaurant")

        # Update user information
        user.name = name
        user.email = email
        user.role = role
        user.restaurant_id = restaurant

        db.session.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("admin.admin_dashboard"))

    # Get all admins for selection
    admins = User.query.filter_by(role="admin").all()
    return render_template("admin/edit_user.html", user=user, admins=admins)


# ---------------------------------------------------------------------------- #
#                         Route to add a new restaurant                        #
# ---------------------------------------------------------------------------- #
@admin.route("/add-restaurant/", methods=["GET", "POST"])
@login_required
@admin_required
def add_restaurant():
    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        admin_id = request.form.get("admin_id")

        # Check if restaurant already exists
        existing_restaurant = Restaurant.query.filter_by(name=name).first()
        if existing_restaurant:
            flash("Restaurant with this name already exists.", "danger")
            return redirect(url_for("admin.add_restaurant"))

        # Create and save new restaurant
        new_restaurant = Restaurant(name=name, address=address, admin_id=admin_id)
        db.session.add(new_restaurant)
        db.session.commit()
        flash("Restaurant added successfully!", "success")
        return redirect(url_for("admin.admin_dashboard"))

    # Get all admins for selection
    context = {
        "current_user": current_user,
        "admins": User.query.filter_by(role="admin").all(),
    }
    return render_template("admin/add_restaurant.html", **context)


@admin.route("edit-restaurant/<int:restaurant_id>", methods=["POST", "GET"])
@login_required
def edit_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")

        # Update restaurant information
        restaurant.name = name
        restaurant.address = address

        db.session.commit()
        flash("Restaurant updated successfully!", "success")
        return redirect(url_for("admin.admin_dashboard"))

    context = {
        "restaurant": Restaurant.query.filter(Restaurant.id == restaurant_id).first(),
        "admins": User.query.filter_by(role="admin").all(),
        "user": current_user,
    }
    return render_template("admin/edit_restaurant.html", **context)


@admin.route("/delete-restaurant/<int:restaurant_id>", methods=["POST"])
@login_required
@admin_required
def delete_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    db.session.delete(restaurant)
    db.session.commit()
    flash("Restaurant deleted successfully!", "success")
    return redirect(url_for("admin.admin_dashboard"))
