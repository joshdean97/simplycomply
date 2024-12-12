from .extensions import db
from sqlalchemy.types import Enum
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin


# Association Table for Sub-user Assignments
class UserRestaurant(db.Model):
    __tablename__ = 'user_restaurant'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', name='fk_userrestaurant_user'), 
        nullable=False
    )
    restaurant_id = db.Column(
        db.Integer, 
        db.ForeignKey('restaurants.id', name='fk_userrestaurant_restaurant'), 
        nullable=False
    )
    role = db.Column(
        db.Enum('admin', 'sub-user', 'viewer', 'editor', name='user_roles'),
        nullable=False
    )

    # Relationships
    user = db.relationship('User', back_populates='assignments')
    restaurant = db.relationship('Restaurant', back_populates='subusers')


# User Model
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(
        db.Enum('admin', 'sub-user', 'viewer', 'editor', name='user_roles'),
        nullable=False
    )

    # Corrected Relationships
    # subusers = db.relationship(
    #     'Subuser',
    #     back_populates='manager',
    #     foreign_keys='Subuser.manager_id'
    # )

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
# class Subuser(db.Model, UserMixin):
#     __tablename__ = 'subusers'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     email = db.Column(db.String(100), unique=True, nullable=False)
#     password_hash = db.Column(db.String(200), nullable=False)
#     role = db.Column(
#         db.Enum('sub-user', 'viewer', 'editor', name='user_roles'),
#         nullable=False
#     )

    # Foreign Key with Named Constraint
    # manager_id = db.Column(
    #     db.Integer, 
    #     db.ForeignKey(
    #         'users.id', 
    #         name='fk_subuser_manager', 
    #         ondelete="CASCADE"
    #     ), 
    #     nullable=False
    # )

    # Corrected Relationship
    # manager = db.relationship(
    #     'User',
    #     back_populates='subusers'
    # )

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
    restaurant_id = db.Column(
        db.Integer, 
        db.ForeignKey('restaurants.id', name='fk_document_restaurant'), 
        nullable=False
    )
