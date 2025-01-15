import re
from functools import wraps
from flask_login import current_user
from flask import flash, redirect, url_for


def check_password_strength(password):
    """
    Checks the strength of a password and returns a message with its rating.

    Criteria:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (!@#$%^&*()-_+=)
    """
    # Define strength criteria
    length_criteria = len(password) >= 8
    uppercase_criteria = bool(re.search(r"[A-Z]", password))
    lowercase_criteria = bool(re.search(r"[a-z]", password))
    digit_criteria = bool(re.search(r"\d", password))
    special_character_criteria = bool(re.search(r"[!@#$%^&*()\-_=+]", password))

    # Evaluate strength
    score = sum(
        [
            length_criteria,
            uppercase_criteria,
            lowercase_criteria,
            digit_criteria,
            special_character_criteria,
        ]
    )

    # Return feedback
    if score == 5:
        return True
    elif score == 4:
        return True
    elif score == 3:
        return False
    else:
        return False


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Access denied: Admins only.", "danger")
            return redirect(url_for("views.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import urllib3


def send_email():
    message = Mail(
        from_email="admin@simplycomply.co",
        to_emails="joshuashepherd877@gmail.com",
        subject="Test Email",
        html_content="<strong>This is a test email.</strong>",
    )

    try:
        # Disable SSL Warnings (Development Only)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Initialize SendGrid client with SSL verification disabled
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))

        # Disable SSL verification for SendGrid's internal HTTP calls
        sg.client.verify = False
        # Send the email
        response = sg.send(message)

        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.body}")
        print(f"Response Headers: {response.headers}")

    except Exception as e:
        print(f"Error sending email: {e}")
