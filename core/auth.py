from flask import Blueprint, render_template
from flask_login import current_user

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
    # handle registration logic
    
    context = {
        'current_user': current_user
    }
    
    return render_template('register.html', **context)

@auth.route('/logout/')
def logout():
    # handle logout logic
    return "Logout Page"

