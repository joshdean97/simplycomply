from .extensions import db
from sqlalchemy.types import Enum
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

from datetime import datetime


# Association Table for Sub-user Assignments
class UserRestaurant(db.Model):
    __tablename__ = "user_restaurant"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    restaurant_id = db.Column(
        db.Integer, db.ForeignKey("restaurants.id"), nullable=False
    )

    # Relationships to User and Restaurant
    user = db.relationship("User", back_populates="user_restaurants")
    restaurant = db.relationship("Restaurant", back_populates="restaurant_users")


# User Model
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    subscription_plan = db.Column(db.String(255))
    total_usage_bytes = db.Column(db.Integer, default=0, nullable=False)

    role = db.Column(
        db.Enum("admin", "sub-user", "viewer", "editor", name="user_roles"),
        nullable=False,
    )

    user_restaurants = db.relationship(
        "UserRestaurant", back_populates="user", cascade="all, delete-orphan"
    )
    restaurants = db.relationship(
        "Restaurant", back_populates="owner", foreign_keys="Restaurant.admin_id"
    )
    manager_id = db.Column(db.Integer, nullable=True)
    restaurant_id = db.Column(db.Integer, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"

    def get_usage(self):
        if self.total_usage_bytes < 1024:
            # return bytes
            return f"{self.total_usage_bytes} bytes"
        elif self.total_usage_bytes < 1024**2:
            # return KB
            return f"{self.total_usage_bytes / 1024:.2f} KB"
        elif self.total_usage_bytes < 1024**3:
            # return MB
            return f"{self.total_usage_bytes / 1024 ** 2:.2f} MB"
        else:
            # return GB
            return f"{self.total_usage_bytes / 1024 ** 3:.2f} GB"

    def get_usage_limit(self):
        """
        Returns the usage limit for the user based on their role and subscription plan.
        If the user is not an admin, it retrieves the usage limit from their manager.
        """
        if self.role != "admin":
            return self.manager_id.get_usage_limit()
        if self.subscription_plan == "basic":
            return 1024**3  # 1 GB in bytes
        elif self.subscription_plan == "standard":
            return 1024**3 * 10  # 10 GB in bytes
        else:
            return 1024**3 * 100  # 100 GB in bytes

    def get_usage_limit_bytes(self):
        if self.subscription_plan == "basic":
            return 1024**5
        elif self.subscription_plan == "standard":
            return 1024**5 * 10
        else:
            return 1024**5 * 100

    def update_usage(self, file_size):
        self.total_usage_bytes += file_size


# Restaurant Model
class Restaurant(db.Model):
    __tablename__ = "restaurants"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_restaurant_admin"),
        nullable=False,
    )

    # Relationships
    owner = db.relationship(
        "User", back_populates="restaurants", foreign_keys=[admin_id]
    )
    restaurant_users = db.relationship(
        "UserRestaurant", back_populates="restaurant", cascade="all, delete-orphan"
    )
    documents = db.relationship("Document", backref="restaurant", lazy=True)


# Document Model
class Document(db.Model):
    __tablename__ = "documents"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(
        db.Enum(
            "Health & Safety",
            "Accident Reports",
            "Fire Safety",
            "HACCP",
            "Allergen Information",
            "Temperature Control Logs",
            "Cleaning Records",
            "Licenses and Permits",
            "Staff Records",
            "Operational Policies",
            name="doc_category",
        ),
        nullable=False,
    )
    file_path = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uploaded_by = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    restaurant_id = db.Column(
        db.Integer,
        db.ForeignKey("restaurants.id", name="fk_document_restaurant"),
        nullable=False,
    )


class Template(db.Model):
    __tablename__ = "templates"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    template_path = db.Column(db.String(200), nullable=False)
    download_count = db.Column(db.Integer)
    category = db.Column(
        db.Enum(
            "Health & Safety",
            "Accident Reports",
            "Fire Safety",
            "HACCP",
            "Allergen Information",
            "Temperature Control Logs",
            "Cleaning Records",
            "Licenses and Permits",
            "Staff Records",
            "Operational Policies",
            name="doc_category",
        ),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=datetime.now())
    created_by = db.Column(db.String(255))
    restaurant_id = db.Column(db.Integer)


alert_recipients = db.Table(
    "alert_recipients",
    db.Column("alert_id", db.Integer, db.ForeignKey("alerts.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )
    restaurant_id = db.Column(
        db.Integer, db.ForeignKey("restaurants.id"), nullable=False
    )
    alert_time = db.Column(db.DateTime, nullable=False)
    repeat = db.Column(db.String(20))

    # Relationships
    restaurant = db.relationship("Restaurant", backref=db.backref("alerts", lazy=True))
    recipients = db.relationship(
        "User", secondary=alert_recipients, backref=db.backref("alerts", lazy=True)
    )

    def __repr__(self):
        return f"<Alert {self.title} for Restaurant {self.restaurant_id}>"
