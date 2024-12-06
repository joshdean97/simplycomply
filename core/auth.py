from flask import Blueprint

# auth blueprint
auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login/', methods=['POST', 'GET'])
def login():
    # handle login logic
    return "Login Page"

@auth.route('/register/', methods=['POST', 'GET'])
def register():
    # handle registration logic
    return "Registration Page"

@auth.route('/logout/')
def logout():
    # handle logout logic
    return "Logout Page"

