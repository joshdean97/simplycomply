# flask imports
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required

# Other library imports
import boto3 
import uuid
import os

# Local imports
from .models import Document, Restaurant
from .extensions import db
from .functions import allowed_file

# Blueprint setup
views = Blueprint('views', __name__)

# index route for landing page 
@views.route('/')
def index():
    
    context = {
        'current_user': current_user,
    }
    return render_template('index.html', **context)

# dashboard route - methods: get; returns user dashboard with compliance document data
@views.route('/dashboard/')
@login_required
def dashboard():
    # Check if the user has a restaurant
    if not current_user.restaurants:
        flash("Please create a restaurant to continue.", "warning")
        return redirect(url_for('views.create_restaurant'))

    context = {
        'current_user': current_user,
        'restaurant': current_user.restaurants,
    }
    return render_template('dashboard.html', **context)

    
@views.route('/create-restaurant/', methods=['GET', 'POST'])
@login_required
def create_restaurant():
    if request.method == 'POST':
        restaurant_name = request.form.get('restaurant_name')

        # Validate restaurant creation
        if not restaurant_name:
            flash("Restaurant name is required.", "danger")
            return redirect(url_for('views.create_restaurant'))

        if Restaurant.query.filter_by(name=restaurant_name).first():
            flash("A restaurant with this name already exists.", "danger")
            return redirect(url_for('views.create_restaurant'))

        # Create restaurant and assign it to the current user
        new_restaurant = Restaurant(name=restaurant_name, admin_id=current_user.id)
        db.session.add(new_restaurant)
        db.session.commit()

        flash("Restaurant created successfully!", "success")
        return redirect(url_for('views.dashboard'))

    return render_template('create_restaurant.html')

# pricing route - methods: get; returns pricing page with information about our services
@views.route('/pricing/')
def pricing():
    return render_template('pricing.html')

# upload route - methods: post; handles file upload, saves it to S3, and adds a Document model entry in the database
@views.route('/upload/', methods=['POST', 'GET'])
@login_required
def upload():
    # allowed docuument extensions        
    if request.method == 'POST':
        uploaded_file = request.files['file']
        
        # create new string from random chars and append filetype to end
        new_filename = uuid.uuid4().hex + '.' + uploaded_file.filename.rsplit('.', 1)[1].lower()    
        
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('No file selected', 'warning')
            return redirect(url_for('views.upload'))

        
        s3 = boto3.resource('s3')
        bucket_name = os.environ.get('BUCKET_NAME')
        
        s3.Bucket(bucket_name).upload_fileobj(uploaded_file, new_filename)
        
        new_file = Document(
            name = uploaded_file.filename,
            file_path ='s3://{}/{}'.format(bucket_name, new_filename),
            uploaded_by = current_user.name,
            category = request.form.get('category'),
            # due_date = request.form.get('due_date'),
            # restaurant_id = current_user.restaurant_id  # Assuming restaurant_id is a foreign key in the User model.
            restaurant_id = 1
        )
        
        db.session.add(new_file)
        db.session.commit()
        flash('File uploaded successfully', 'success')
        return redirect(url_for('views.dashboard'))
            
    
    context = {
        'current_user': current_user
    }
    return render_template('upload.html', **context)

@views.route('/settings/')

@login_required
def settings():
    return 'settings'