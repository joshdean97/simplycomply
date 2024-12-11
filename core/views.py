from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required

import boto3 
import uuid

from .models import Document
from .extensions import db

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

@views.route('/upload/', methods=['POST', 'GET'])
@login_required
def upload():
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    
    if request.method == 'POST':
        uploaded_file = request.files['file']
        new_filename = uuid.uuid4().hex + '.' + uploaded_file.filename.rsplit('.', 1)[1].lower()    
        
        if not allowed_file(uploaded_file.filename):
                return "File not allowed"
        
        s3 = boto3.resource('s3')
        bucket_name = 'simply-comply'
        
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