from .extensions import db
from sqlalchemy.types import Enum
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin


# Association Table for Sub-user Assignments
class UserRestaurant(db.Model):
    __tablename__ = 'user_restaurant'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    role = db.Column(
        Enum('admin', 'sub-user', 'viewer', 'editor', name='user_roles'),
        nullable=False
    )

    # Relationships
    user = db.relationship('User', back_populates='assignments')
    restaurant = db.relationship('Restaurant', back_populates='subusers')


# User Model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(
        Enum('admin', 'sub-user', 'viewer', 'editor', name='user_roles'),
        nullable=False
    )

    # Relationships
    assignments = db.relationship('UserRestaurant', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Restaurant Model
class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    owner = db.relationship('User', backref='restaurant', foreign_keys=[admin_id])
    subusers = db.relationship('UserRestaurant', back_populates='restaurant')
    documents = db.relationship('Document', backref='restaurant', lazy=True)


# Document Model
class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(
        Enum('Hygiene', 'Health & Safety', 'Training', 'Licenses', name='doc_category'),
        nullable=False
    )
    file_path = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uploaded_by = db.Column(db.String(100), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
