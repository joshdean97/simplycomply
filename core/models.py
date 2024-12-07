from .extensions import db
from sqlalchemy.sql import func

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(55))
    last_name = db.Column(db.String(55))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    restaurants = db.relationship('Restaurant', backref='user')  # Add backref for bidirectional relationship
    
class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Foreign key linking to User
    subusers = db.relationship('Subuser', backref='restaurant')
    documents = db.relationship('Document', backref='restaurant')  
    
class Subuser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id')) 
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    first_name = db.Column(db.String(55))
    last_name = db.Column(db.String(55))
    
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))
    type = db.Column(db.String(255), default=None)
    title = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    expiry_date = db.Column(db.DateTime(timezone=True), default=None)