from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    send_file,
    flash,
)

from fpdf import FPDF
from io import BytesIO
from flask_login import login_required, current_user

from ..const import CATEGORIES
from ..models import Alert, User
from ..extensions import db

from datetime import datetime


# Blueprint initialization
create = Blueprint("create", __name__, url_prefix="/create")


@create.route("/")
@login_required
def create_index():
    return render_template("create/create.html")


@create.route("/checklist/", methods=["GET", "POST"])
@login_required
def create_checklist():
    if request.method == "POST":
        tasks = request.form.getlist("items")
        category = request.form.get("category")
        name = request.form.get("name")

        if not tasks:
            flash("Please enter a category", "info")
            return redirect(url_for("create.create_checklist"))
        if not name:
            name = "Untitled Checklist"
        if not tasks:
            flash("Please enter at least one task", "info")
            return redirect(url_for("create.create_checklist"))

        # Create PDF class
        class PDF(FPDF):
            def header(self):
                self.set_font("Arial", "B", 15)
                self.cell(0, 10, name, 0, 1, "C")
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font("Arial", "I", 8)
                self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

        # Create a PDF object
        pdf = PDF()
        pdf.add_page()

        # Set font for the table
        pdf.set_font("Arial", "B", 10)

        # Define the headers
        headers = ["Task", "M", "T", "W", "T", "F", "S", "S"]

        # Set column widths
        col_widths = [50, 20, 20, 20, 20, 20, 20, 20]

        # Create the header row
        for i in range(len(headers)):
            pdf.cell(col_widths[i], 10, headers[i], 1, 0, "C")
        pdf.ln()

        # Set font for the body
        pdf.set_font("Arial", "", 10)

        # Create the body rows
        for task in tasks:
            pdf.cell(col_widths[0], 10, task, 1)
            for _ in range(7):  # 7 blank columns for M, T, W, T, F, S, S
                pdf.cell(col_widths[1], 10, "", 1)
            pdf.ln()

        # Save PDF to a file-like object
        pdf_output = BytesIO()
        pdf_content = pdf.output(dest="S").encode("latin1")  # Correct output method
        pdf_output.write(pdf_content)
        pdf_output.seek(0)  # Move to the beginning of the BytesIO buffer

        # Send the PDF file for download
        return send_file(
            pdf_output,
            as_attachment=True,
            download_name=f"{name.replace(' ', '_')}_checklist.pdf",
            mimetype="application/pdf",
        )
    context = {"categories": CATEGORIES}
    return render_template("create.html", **context)


@create.route("/alerts/", methods=["GET", "POST"])
@login_required
def create_alerts():
    # Query managed users
    managed_users = User.query.filter(User.manager_id == current_user.id).all()

    if request.method == "POST":
        title = request.form.get("title")
        message = request.form.get("message")
        recipients = request.form.getlist("recipients")  # List of user IDs
        repeat = request.form.get("repeat")
        date = request.form.get("date")  # Extract the selected date
        time = request.form.get("time")  # Extract the selected time
        restaurant_id = request.form.get("restaurant_id")

        # Validation
        if (
            not title
            or not message
            or not recipients
            or not repeat
            or not date
            or not time
        ):
            flash("All fields are required.", "danger")
            return redirect(url_for("alerts.create_alert"))

        # Combine date and time into a single datetime object
        try:
            alert_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for("alerts.create_alert"))

        # Create new Alert
        new_alert = Alert(
            title=title,
            message=message,
            repeat=repeat,
            alert_time=alert_datetime,  # Save the combined datetime
            restaurant_id=restaurant_id,
        )

        # Add recipients
        for user_id in recipients:
            user = User.query.get(user_id)
            if user:
                new_alert.recipients.append(user)

        # Save to DB
        db.session.add(new_alert)
        db.session.commit()

        flash("Alert created successfully!", "success")
        return redirect(url_for("views.dashboard"))

    # Pass managed_users to the template
    return render_template("create/create_alert.html", managed_users=managed_users)


@create.route("/docs/", methods=["GET", "POST"])
@login_required
def create_docs():
    managed_users = User.query.filter(User.manager_id == current_user.id).all()
    if request.method == "POST":
        tasks = request.form.getlist("items")
        category = request.form.get("category")
        name = request.form.get("name")

        if not tasks:
            flash("Please enter a category", "info")
            return redirect(url_for("create.create_checklist"))
        if not name:
            name = "Untitled Checklist"
        if not tasks:
            flash("Please enter at least one task", "info")
            return redirect(url_for("create.create_checklist"))

        # Create PDF class
        class PDF(FPDF):
            def header(self):
                self.set_font("Arial", "B", 15)
                self.cell(0, 10, name, 0, 1, "C")
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font("Arial", "I", 8)
                self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

        # Create a PDF object
        pdf = PDF()
        pdf.add_page()

        # Set font for the table
        pdf.set_font("Arial", "B", 10)

        # Define the headers
        headers = ["Task", "M", "T", "W", "T", "F", "S", "S"]

        # Set column widths
        col_widths = [50, 20, 20, 20, 20, 20, 20, 20]

        # Create the header row
        for i in range(len(headers)):
            pdf.cell(col_widths[i], 10, headers[i], 1, 0, "C")
        pdf.ln()

        # Set font for the body
        pdf.set_font("Arial", "", 10)

        # Create the body rows
        for task in tasks:
            pdf.cell(col_widths[0], 10, task, 1)
            for _ in range(7):  # 7 blank columns for M, T, W, T, F, S, S
                pdf.cell(col_widths[1], 10, "", 1)
            pdf.ln()

        # Save PDF to a file-like object
        pdf_output = BytesIO()
        pdf_content = pdf.output(dest="S").encode("latin1")  # Correct output method
        pdf_output.write(pdf_content)
        pdf_output.seek(0)  # Move to the beginning of the BytesIO buffer

        # Send the PDF file for download
        return send_file(
            pdf_output,
            as_attachment=True,
            download_name=f"{name.replace(' ', '_')}_checklist.pdf",
            mimetype="application/pdf",
        )
    context = {
        "categories": CATEGORIES,
        "managed_users": managed_users,
    }

    return render_template("create_docs.html", **context)


@create.route("/incidents/", methods=["GET", "POST"])
@login_required
def create_incident():
    if request.method == "POST":
        tasks = request.form.getlist("items")
        category = request.form.get("category")
        name = request.form.get("name")

        if not tasks:
            flash("Please enter a category", "info")
            return redirect(url_for("create.create_checklist"))
        if not name:
            name = "Untitled Checklist"
        if not tasks:
            flash("Please enter at least one task", "info")
            return redirect(url_for("create.create_checklist"))

        # Create PDF class
        class PDF(FPDF):
            def header(self):
                self.set_font("Arial", "B", 15)
                self.cell(0, 10, name, 0, 1, "C")
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font("Arial", "I", 8)
                self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

        # Create a PDF object
        pdf = PDF()
        pdf.add_page()

        # Set font for the table
        pdf.set_font("Arial", "B", 10)

        # Define the headers
        headers = ["Task", "M", "T", "W", "T", "F", "S", "S"]

        # Set column widths
        col_widths = [50, 20, 20, 20, 20, 20, 20, 20]

        # Create the header row
        for i in range(len(headers)):
            pdf.cell(col_widths[i], 10, headers[i], 1, 0, "C")
        pdf.ln()

        # Set font for the body
        pdf.set_font("Arial", "", 10)

        # Create the body rows
        for task in tasks:
            pdf.cell(col_widths[0], 10, task, 1)
            for _ in range(7):  # 7 blank columns for M, T, W, T, F, S, S
                pdf.cell(col_widths[1], 10, "", 1)
            pdf.ln()

        # Save PDF to a file-like object
        pdf_output = BytesIO()
        pdf_content = pdf.output(dest="S").encode("latin1")  # Correct output method
        pdf_output.write(pdf_content)
        pdf_output.seek(0)  # Move to the beginning of the BytesIO buffer

        # Send the PDF file for download
        return send_file(
            pdf_output,
            as_attachment=True,
            download_name=f"{name.replace(' ', '_')}_checklist.pdf",
            mimetype="application/pdf",
        )
    context = {"categories": CATEGORIES}
    return render_template("create_incident.html", **context)
