from .extensions import db

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
