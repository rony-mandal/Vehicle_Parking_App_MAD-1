from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='User')
    
    # This defines the other side of the relationship from Reservation back to User.
    reservations = db.relationship('Reservation', backref='user', lazy=True)

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False) 
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    maximum_number_of_spots = db.Column(db.Integer, nullable=False)
    
    # This relationship correctly cascades deletions from a Lot to its Spots.
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade="all, delete-orphan")

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False) 
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), nullable=False, default='A')
    
    # This defines the other side of the relationship from Reservation back to ParkingSpot.
    reservations = db.relationship('Reservation', backref='spot', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('lot_id', 'spot_number', name='unique_spot_in_lot'),)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # RECTIFIED: Added ondelete='CASCADE' to the ForeignKeys.
    # This tells the database that if a User or ParkingSpot is deleted,
    # the corresponding Reservation records should also be deleted automatically.
    # This is the key fix to prevent orphaned records and crashes.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id', ondelete='CASCADE'), nullable=False)
    
    parking_timestamp = db.Column(db.DateTime, nullable=False)
    leaving_timestamp = db.Column(db.DateTime, nullable=True) 
    parking_cost = db.Column(db.Float, nullable=True) 
    
    # RECTIFIED: Removed the relationships from here.
    # The relationships are now defined on the parent models (User, ParkingSpot)
    # using the 'backref' property, which is a cleaner approach.