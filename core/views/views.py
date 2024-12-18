# flask imports
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, send_file
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash

# Other library imports
import boto3 
import uuid
import os
from io import BytesIO
from datetime import datetime

# Local imports
from ..models import Document, Restaurant
from ..extensions import db
from ..functions import allowed_file
from ..const import CATEGORIES

# reportlab imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors


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
@views.route('/dashboard/', methods=['GET', 'POST'])
@login_required
def dashboard():
    # Handle POST request for restaurant selection
    if request.method == 'POST':
        restaurant_id = request.form.get('restaurant_id')
        
        # Ensure the selected restaurant belongs to the current user
        selected_restaurant = Restaurant.query.filter_by(
            id=restaurant_id, admin_id=current_user.id
        ).first()

        if not selected_restaurant:
            flash("Invalid restaurant selection.", "danger")
            return redirect(url_for('views.dashboard'))
        
        # Store selection in session
        session['selected_restaurant_id'] = selected_restaurant.id
        flash(f"Switched to {selected_restaurant.name}.", "success")
        return redirect(url_for('views.dashboard'))

    # Handle GET request
    if len(current_user.restaurants) > 0:
        selected_restaurant_id = session.get('selected_restaurant_id')
        selected_restaurant = Restaurant.query.filter_by(
            id=selected_restaurant_id, admin_id=current_user.id
        ).first() or current_user.restaurants[0]
        
        context = {
            'selected_restaurant': selected_restaurant,
            'selected_restaurant_id': selected_restaurant.id,
            'categories': CATEGORIES
        }

        return render_template(
            'dashboard.html',
            **context
        )
    else:
        flash("You haven't assigned a restaurant yet.", "info")
        return redirect(url_for('views.create_restaurant'))
    
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
    # Allowed document extensions
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    if request.method == 'POST':
        uploaded_file = request.files.get('file')

        if not uploaded_file or uploaded_file.filename == '':
            flash('No file selected', 'warning')
            return redirect(url_for('views.upload'))

        if not allowed_file(uploaded_file.filename):
            flash('File type not allowed', 'danger')
            return redirect(url_for('views.upload'))

        # Generate a unique filename
        new_filename = f"{uuid.uuid4().hex}.{uploaded_file.filename.rsplit('.', 1)[1].lower()}"
        
        file_size = len(uploaded_file.read()) # GET FILE SIZE IN BYTES
        uploaded_file.seek(0) #reset file pointer after reading

        # Connect to S3
        s3 = boto3.resource('s3')
        bucket_name = os.environ.get('BUCKET_NAME')

        # Build file key and file path
        restaurant_id = request.form.get('restaurant')
        category = request.form.get('category')
        file_key = f"restaurant_{restaurant_id}/uploads/{category}/{new_filename}"
        file_path = f"https://{bucket_name}.s3.eu-west-1.amazonaws.com/{file_key}"

        try:
            # Upload to S3
            s3.Bucket(bucket_name).upload_fileobj(uploaded_file, file_key)

            # Save the file record in the database
            new_file = Document(
                name=request.form.get('title'),
                file_path=file_path,
                uploaded_by=current_user.name,
                category=category,
                file_size = file_size,
                restaurant_id=restaurant_id
            )

            db.session.add(new_file)
            db.session.commit()
            print(new_file.file_size + " bytes")
            flash('File uploaded successfully', 'success')
            return redirect(url_for('views.dashboard'))

        except Exception as e:
            flash(f"Upload failed: {str(e)}", 'danger')
            return redirect(url_for('views.upload'))

    # Render form for GET requests
    context = {
        'current_user': current_user,
        'categories': CATEGORIES
    }
    return render_template('upload.html', **context)

@views.route('/create/', methods=['GET', 'POST'])
@login_required  # Ensure that only authenticated users can access this route
def create_compliance():
    return '<h1>Create</h1>'

@views.route('/profile/', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate form data
        if not name or not email:
            flash('Name and Email are required.', 'danger')
            return redirect(url_for('views.profile'))

        # Update current user details
        current_user.name = name
        current_user.email = email

        if password:
            current_user.password_hash = generate_password_hash(password)

        # Commit changes to the database
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'danger')
            db.session.rollback()

        return redirect(url_for('views.profile'))

    return render_template('profile.html')

@views.route('/generate-report/', methods=['POST'])
@login_required
def generate_report():
    category = request.form.get('category')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    # Query documents
    query = Document.query.filter(
        Document.restaurant_id == current_user.restaurant_id,
        Document.uploaded_at.between(start_date, end_date)
    )

    if category:
        query = query.filter(Document.category == category)

    documents = query.all()

    if not documents:
        flash("No documents found for the selected criteria.", "warning")
        return redirect(url_for('views.dashboard'))

    # Generate PDF report
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Add table header
    data = [["Name", "Category", "Uploaded By", "Uploaded At"]]
    for doc in documents:
        data.append([
            doc.name, 
            doc.category, 
            doc.uploaded_by, 
            doc.uploaded_at.strftime("%Y-%m-%d")
        ])

    # Define table style
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    pdf.build(elements)

    buffer.seek(0)

    # Send the generated file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mimetype='application/pdf'
    )

@views.route('/templates/')
@login_required
def templates():
    return render_template('templates.html')

@views.route('/settings/')

@login_required
def settings():
    return 'settings'