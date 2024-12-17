from .extensions import db
from sqlalchemy.types import Enum
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin


# Association Table for Sub-user Assignments
# class UserRestaurant(db.Model):
#     __tablename__ = 'user_restaurant'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(
#         db.Integer, 
#         db.ForeignKey('users.id', name='fk_userrestaurant_user'), 
#         nullable=False
#     )
#     restaurant_id = db.Column(
#         db.Integer, 
#         db.ForeignKey('restaurants.id', name='fk_userrestaurant_restaurant'), 
#         nullable=False
#     )
#     role = db.Column(
#         db.Enum('admin', 'sub-user', 'viewer', 'editor', name='user_roles'),
#         nullable=False
#     )

#     # Relationships
#     user = db.relationship('User', back_populates='assignments')
#     restaurant = db.relationship('Restaurant', back_populates='subusers')


user_categories = db.Table(
    'document_categories',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'))
)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Category: {self.name}>'

# User Model
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    subscription_plan = db.Column(db.String(255), default="basic", nullable=False)
    categories = db.relationship('Category', secondary=user_categories, backref='categories')

    role = db.Column(
        db.Enum('admin', 'sub-user', 'viewer', 'editor', name='user_roles'),
        nullable=False
    )

    assignments = db.relationship(
        'UserRestaurant',
        back_populates='user'
    )
    restaurants = db.relationship(
        'Restaurant', 
        back_populates='owner', 
        foreign_keys='Restaurant.admin_id'
    )
    manager_id = db.Column(db.String(15), nullable=True)
    restaurant_id = db.Column(db.String(15), nullable=True)

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
    admin_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', name='fk_restaurant_admin'), 
        nullable=False
    )

    # Relationships
    owner = db.relationship('User', back_populates='restaurants', foreign_keys=[admin_id])
    subusers = db.relationship('UserRestaurant', back_populates='restaurant')
    documents = db.relationship('Document', backref='restaurant', lazy=True)


# Document Model
class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(
        db.Enum(
            'Hygiene', 
            'Health & Safety', 
            'Training', 
            'Licenses', 
            'Compliance',
            'Documentation',
            'Cleaning Records',
            'Inspection Reports',
            'Staff Records',
            name='doc_category'
        ),
        nullable=False
    )
    file_path = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uploaded_by = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    restaurant_id = db.Column(
        db.Integer, 
        db.ForeignKey('restaurants.id', name='fk_document_restaurant'), 
        nullable=False
    )
    
class Template(db.Model):
    __tablename__ = 'templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    template_path = db.Column(db.String(200), nullable=False)
    download_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
