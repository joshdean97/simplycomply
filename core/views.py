from flask import Blueprint, render_template
from flask_login import current_user, login_required

views = Blueprint('views', __name__)

@views.route('/')
def index():
    
    context = {
        'current_user': current_user,
    }
    return render_template('index.html', **context)

@views.route('/dashboard/')
@login_required
def dashboard():
    context = {
        'current_user': current_user
    }
    
    return render_template('dashboard.html', **context)

@views.route('/pricing/')
def pricing():
    return render_template('pricing.html')