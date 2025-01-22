# flask imports
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    session,
    send_file,
    jsonify,
)
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash
from flask_mailman import EmailMessage
import stripe

# Other library imports
import boto3
import uuid
import os
from io import BytesIO
from datetime import datetime
import json

# Local imports
from ..models import Document, Restaurant, Template, Alert, User
from ..extensions import db
from ..const import CATEGORIES
from ..functions import allowed_file

from PyPDF2 import PdfMerger


# Blueprint setup
views = Blueprint("views", __name__)


# index route for landing page
@views.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("views.dashboard"))
    else:
        context = {
            "current_user": current_user,
        }
        return render_template("index.html", **context)


# dashboard route - methods: get; returns user dashboard with compliance document data
@views.route("/dashboard/", methods=["GET", "POST"])
@login_required
def dashboard():
    # Handle POST request for restaurant selection
    if request.method == "POST":
        restaurant_id = request.form.get("restaurant_id")

        # Ensure the selected restaurant belongs to the current user
        selected_restaurant = Restaurant.query.filter_by(
            id=restaurant_id, admin_id=current_user.id
        ).first()

        if not selected_restaurant:
            flash("Invalid restaurant selection.", "danger")
            return redirect(url_for("views.dashboard"))

        # Store selection in session
        session["selected_restaurant_id"] = selected_restaurant.id
        flash(f"Switched to {selected_restaurant.name}.", "success")
        return redirect(url_for("views.dashboard"))

    # Handle GET request
    if len(current_user.restaurants) > 0:
        selected_restaurant_id = session.get("selected_restaurant_id")
        selected_restaurant = (
            Restaurant.query.filter_by(id=selected_restaurant_id).first()
            or current_user.restaurants[0]
        )
        alerts = (
            Alert.query.filter(Alert.restaurant_id == selected_restaurant_id)
            .order_by(Alert.alert_time)
            .all()
        )

        context = {
            "now": datetime.now(),
            "selected_restaurant": selected_restaurant,
            "selected_restaurant_id": selected_restaurant.id,
            "categories": CATEGORIES,
            "title": "Dashboard",
            "alerts": alerts,
        }

        return render_template("dashboard.html", **context)
    else:
        flash("You haven't assigned a restaurant yet.", "info")
        return redirect(url_for("admin.add_restaurant"))


@views.route("/create-restaurant/", methods=["GET", "POST"])
@login_required
def create_restaurant():
    if request.method == "POST":
        restaurant_name = request.form.get("restaurant_name")

        # Validate restaurant creation
        if not restaurant_name:
            flash("Restaurant name is required.", "danger")
            return redirect(url_for("views.create_restaurant"))

        if Restaurant.query.filter_by(name=restaurant_name).first():
            flash("A restaurant with this name already exists.", "danger")
            return redirect(url_for("views.create_restaurant"))

        # Create restaurant and assign it to the current user
        new_restaurant = Restaurant(name=restaurant_name, admin_id=current_user.id)
        db.session.add(new_restaurant)
        db.session.commit()

        flash("Restaurant created successfully!", "success")
        return redirect(url_for("views.dashboard"))

    return render_template("create_restaurant.html")


# pricing route - methods: get; returns pricing page with information about our services
@views.route("/pricing/")
def pricing():
    return render_template("pricing.html")


# upload route - methods: post; handles file upload, saves it to S3, and adds a Document model entry in the database
@views.route("/upload/", methods=["POST", "GET"])
@login_required
def upload():
    if request.method == "POST":
        uploaded_file = request.files.get("file")

        if not uploaded_file or uploaded_file.filename == "":
            flash("No file selected", "warning")
            return redirect(url_for("views.upload"))

        if not allowed_file(uploaded_file.filename):
            flash("File type not allowed", "danger")
            return redirect(url_for("views.upload"))

        # Generate a unique filename
        new_filename = (
            f"{uuid.uuid4().hex}.{uploaded_file.filename.rsplit('.', 1)[1].lower()}"
        )

        file_size = len(uploaded_file.read())  # GET FILE SIZE IN BYTES
        uploaded_file.seek(0)  # reset file pointer after reading

        # Connect to S3
        s3 = boto3.resource("s3")
        bucket_name = os.environ.get("BUCKET_NAME")

        # Build file key and file path
        restaurant_id = session.get("selected_restaurant_id")
        category = request.form.get("category")
        file_key = f"restaurant_{restaurant_id}/uploads/{category}/{new_filename}"
        file_path = f"https://{bucket_name}.s3.eu-west-1.amazonaws.com/{file_key}"

        try:
            # Upload to S3
            s3.Bucket(bucket_name).upload_fileobj(uploaded_file, file_key)

            # Save the file record in the database
            new_file = Document(
                name=request.form.get("title"),
                file_path=file_path,
                uploaded_by=current_user.name,
                category=category,
                file_size=file_size,
                restaurant_id=restaurant_id,
            )

            db.session.add(new_file)
            db.session.commit()
            print(f"{new_file.file_size} bytes")
            # if not admin, add usage to manager usage, else add to user usage
            if current_user.role == "admin":
                current_user.total_usage_bytes += int(new_file.file_size)
            else:
                manager = User.query.get(current_user.manager_id)
                if manager:
                    manager.total_usage_bytes += int(new_file.file_size)
            db.session.commit()
            flash("File uploaded successfully", "success")
            return redirect(url_for("views.dashboard"))

        except Exception as e:
            flash(f"Upload failed: {str(e)}", "danger")
            return redirect(url_for("views.upload"))

    # Render form for GET requests
    context = {"current_user": current_user, "categories": CATEGORIES}
    return render_template("upload.html", **context)


@views.route("/delete_document/<int:document_id>", methods=["POST"])
@login_required
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)
    file_size = document.file_size

    # Delete the file from S3
    try:
        s3 = boto3.client("s3")
        bucket_name = os.environ.get("BUCKET_NAME")
        file_key = document.file_path.split(
            f"https://{bucket_name}.s3.eu-west-1.amazonaws.com/"
        )[1]
        s3.delete_object(Bucket=bucket_name, Key=file_key)

        # if not admin, remove usage from manager usage, else remove from user usage
        if current_user.role == "admin":
            current_user.total_usage_bytes -= int(file_size)
        else:
            manager = User.query.get(current_user.manager_id)
            if manager:
                manager.total_usage_bytes -= int(file_size)
        db.session.commit()

    except Exception as e:
        flash(f"Error deleting file from S3: {str(e)}", "danger")
        return redirect(url_for("views.dashboard"))

    # Delete the document from the database
    db.session.delete(document)
    db.session.commit()

    flash("Document deleted successfully.", "success")
    return redirect(url_for("views.dashboard"))


from ..functions import convert_bytes


@views.route("/profile/", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Validate form data
        if not name or not email:
            flash("Name and Email are required.", "danger")
            return redirect(url_for("views.profile"))

        # Update current user details
        current_user.name = name
        current_user.email = email

        if password:
            current_user.password_hash = generate_password_hash(password)

        # Commit changes to the database
        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            flash(f"Error updating profile: {str(e)}", "danger")
            db.session.rollback()

        return redirect(url_for("views.profile"))

    usage_str = current_user.get_usage()  # Example: "12.45 GB"

    # Extract the numeric part from the string
    usage_value = float(usage_str.split()[0])  # This gets the number before the unit

    user_usage_limit = current_user.get_usage_limit()
    print(user_usage_limit)

    context = {
        "usage": usage_value,  # Now a float (e.g., 12.45)
        "usage_display": usage_str,  # Keep the original formatted string
        "usage_limit": user_usage_limit,
        "convert_bytes": convert_bytes,
    }

    return render_template("profile.html", **context)


@views.route("/generate-report/", methods=["POST", "GET"])
@login_required
def generate_report():
    if request.method == "POST":
        # get selected restaurant from session
        selected_restaurant_id = session.get("selected_restaurant_id")
        selected_categories = request.form.getlist("categories")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        # Validate date format
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(url_for("views.dashboard"))

        print(selected_categories)

        # Query documents
        query = Document.query.filter(
            Document.restaurant_id == selected_restaurant_id,
            Document.uploaded_at.between(start_date, end_date),
            Document.category.in_(selected_categories),
        )

        documents = Document.query.all()

        # Check if any documents were found
        if not documents:
            flash("No documents found for the selected criteria.", "warning")
            return redirect(url_for("views.dashboard"))

    # Initialize PDF merger
    merger = PdfMerger()
    s3 = boto3.client("s3")

    for doc in documents:
        if doc.file_path.lower().endswith(".pdf"):
            try:
                # Extract bucket and key from S3 URL
                bucket_name = "simply-comply"
                file_key = doc.file_path.split(
                    f"https://{bucket_name}.s3.eu-west-1.amazonaws.com/"
                )[1]

                # Download file from S3
                file_stream = BytesIO()
                s3.download_fileobj(bucket_name, file_key, file_stream)
                file_stream.seek(0)

                # Append file to the merger
                merger.append(file_stream)
            except Exception as e:
                flash(f"Error processing {doc.name}: {str(e)}", "danger")

    # Generate merged file
    output_file = BytesIO()
    merger.write(output_file)
    merger.close()

    output_file.seek(0)

    return send_file(
        output_file,
        as_attachment=True,
        download_name=f"Collated_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mimetype="application/pdf",
    )


@views.route("/templates/")
@login_required
def templates():
    if request.method == "POST":
        template_file = request.form.get("template_file")
        template_name = request.form.get("template_name")
        restaurant_id = request.form.get("restaurant_id")
        category = request.form.get("category")

        s3 = boto3.client("s3")
        bucket_name = os.environ.get("BUCKET_NAME")

        # Upload the template file to S3
        file_key = f"restaurant_{restaurant_id}/templates/{template_file}"
        s3.upload_fileobj(template_file, bucket_name, file_key)

        # Save the template record in the database
        new_template = Template(
            name=template_name,
            file_path=f"https://{bucket_name}.s3.eu-west-1.amazonaws.com/{file_key}",
            restaurant_id=restaurant_id,
            category=category,
            created_by=current_user.name,
            uploaded_at=datetime.now(),
        )
        db.session.add(new_template)
        db.session.commit()
        flash("Successfully created", "success")

        return redirect(url_for("views.templates"))

    context = {
        "categories": CATEGORIES,
        "current_user": current_user,
        "templates": Template.query.all(),
    }
    return render_template("templates.html", **context)


@views.route("/get-usage/")
@login_required
def get_usage_in_gb():
    usage_str = current_user.get_usage()  # Example: "12.45 GB"

    # Extract the numeric part from the string
    usage_value = float(usage_str.split()[0])  # This gets the number before the unit

    context = {
        "usage": usage_value,  # Now a float (e.g., 12.45)
        "usage_display": usage_str,  # Keep the original formatted string
    }

    return render_template("includes/usage.html", **context)


@views.route("/choose-plan/<int:user_id>/", methods=["GET"])
@login_required
def choose_plan(user_id):
    user = User.query.get_or_404(user_id)
    context = {
        "user": user,
    }
    return render_template("choose_plan.html", **context)


@views.route("/upgrade-plan/<int:user_id>/", methods=["POST"])
@login_required
def upgrade_plan(user_id):
    user = User.query.get_or_404(user_id)
    plan = request.form.get("plan")

    if plan == "basic":
        user.subscription_plan = "basic"
    elif plan == "standard":
        user.subscription_plan = "standard"
    else:
        user.subscription_plan = "premium"

    print(plan)

    db.session.commit()
    flash("Plan upgraded successfully!", "success")
    return redirect(url_for("views.dashboard"))


# stripe
@views.route("/create-checkout-session", methods=["POST"])
@login_required
def create_checkout_session():
    plan = request.form.get("plan")  # Get the selected plan (basic, standard, premium)

    # Define the Stripe price IDs (from your Stripe Dashboard)
    plan_prices = {
        "basic": "price_1Qk1QX2M7cCdaKqq3Ck5Smy2",  # Replace with your Stripe Price ID
        "standard": "price_1Qk1gV2M7cCdaKqqh1g2AZNq",
        "enterprise": "price_1Qk1gy2M7cCdaKqqNC4SnWPM",
    }

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": plan_prices[plan],
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=url_for("views.payment_success", _external=True),
            cancel_url=url_for("views.payment_cancel", _external=True),
            customer_email=current_user.email,  # Link the payment to the logged-in user
        )

        # Update the user's subscription plan in the database
        current_user.subscription_plan = plan
        db.session.commit()

        return redirect(checkout_session.url)
    except Exception as e:
        return jsonify(error=str(e)), 400


@views.route("/payment-success")
@login_required
def payment_success():
    # Update user subscription in the database if needed
    flash("Payment successful! Your subscription has been activated.", "success")
    return redirect(url_for("views.profile"))


@views.route("/payment-cancel")
@login_required
def payment_cancel():
    flash("Payment was cancelled. Please try again.", "warning")
    return redirect(url_for("views.choose_plan", user_id=current_user.id))


@views.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    event = None

    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        return "Invalid payload", 400

    # Handle successful payment
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session["customer_email"]

        # Update the user's subscription in the database
        user = User.query.filter_by(email=customer_email).first()
        if user:
            user.subscription_plan = session["display_items"][0]["plan"]["nickname"]
            db.session.commit()

    return "", 200
