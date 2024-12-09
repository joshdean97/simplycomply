from .extensions import db
from sqlalchemy.types import Enum

from werkzeug.security import check_password_hash, generate_password_hash


# User Model (Admins and Sub-users)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'sub-user'

    # Password methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Relationships
    restaurants = db.relationship('Restaurant', backref='admin', lazy=True)
    assignments = db.relationship('UserRestaurant', back_populates='user', lazy=True)

# Restaurant Model
class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Admin who owns this restaurant
    
    # Relationships
    documents = db.relationship('Document', backref='restaurant', lazy=True)  # Documents for the restaurant
    subusers = db.relationship('UserRestaurant', back_populates='restaurant', lazy=True)  # Sub-users assigned here

# UserRestaurant Association Table (For Sub-user Assignments)
class UserRestaurant(db.Model):
    __tablename__ = 'user_restaurant'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    role = db.Column(Enum('admin', 'sub-user', 'viewer', 'editor', name='user_roles'), nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='assignments')
    restaurant = db.relationship('Restaurant', back_populates='subusers')

# Document Model (Compliance Documents)
class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)  # Path to the stored document
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uploaded_by = db.Column(db.String(100), nullable=False)
    category = db.Column(Enum('Hygiene', 'Health & Safety', 'Training', 'Licenses', name='doc_category'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active')  # e.g., 'active', 'expired'
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)  # Associated restaurant
    
    __table_args__ = (
        db.Index('ix_document_category', 'category'),
    )

