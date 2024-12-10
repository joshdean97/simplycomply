from flask import Blueprint, render_template, request, url_for, flash, redirect
from flask_login import current_user
from werkzeug.security import generate_password_hash

from .models import User
from .extensions import db
from .functions import check_password_strength

# auth blueprint
auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login/', methods=['POST', 'GET'])
def login():
    # handle login logic
    
    context = {
        'current_user': current_user
    }
    
    return render_template('login.html', **context)

@auth.route('/register/', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate inputs
        if len(first_name) < 2:
            flash('First name must be at least 2 characters.', 'error')
        elif len(last_name) < 2:
            flash('Last name must be at least 2 characters.', 'error')
        elif not email:
            flash('Email is required.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif not check_password_strength(password):
            flash('Password is too weak. It must be at least 8 characters long and include uppercase letters, lowercase letters, numbers, and special characters.', 'error')
        else:
            # Add new user to the database
            hashed_password = generate_password_hash(password)
            new_user = User(
                name=f"{first_name} {last_name}",
                email=email,
                password_hash=hashed_password,
                role='admin'  # Default to 'admin' role; adjust as needed
            )
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))    
    context = {
        
    }
    
    return render_template('register.html', **context)

@auth.route('/logout/')
def logout():
    # handle logout logic
    return "Logout Page"

