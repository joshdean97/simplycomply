from flask import Blueprint, render_template
from flask_login import current_user, login_required

views = Blueprint('views', __name__)

@views.route('/')
def index():
    return render_template('index.html', current_user=current_user)

