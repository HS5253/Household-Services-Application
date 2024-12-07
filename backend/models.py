
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

# User Table
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.Integer, nullable=False)  # Using Enum for the role

# Customer Table
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    profile_status = db.Column(db.Boolean, nullable = False, default = 0) #0-Active , 1-Blocked
    user = db.relationship('User',backref='customer',cascade='all,delete',lazy=True)
    c_servicerequests = db.relationship('ServiceRequest', back_populates='customer', cascade='all,delete',lazy=True)


# Service Professional Table
class ServiceProfessional(db.Model):
    __tablename__ = "service_professionals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False) 
    full_name = db.Column(db.String, nullable=False)
    service_id = db.Column(db.String, db.ForeignKey('services.id'), nullable=False)
    description = db.Column(db.Text)
    experience = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable = False)
    reviews = db.Column(db.Integer, default = 0)
    available_status = db.Column(db.Boolean, nullable = False,default=1)#1=Available, 0- Not Available
    profile_documents = db.Column(db.String, nullable=False)
    profile_status = db.Column(db.Boolean, nullable = False, default = 0) #0-Active , 1-Blocked
    verification = db.Column(db.String,default="pending")
    user = db.relationship('User',backref='service_professional',cascade='all,delete',lazy=True)
    sp_servicerequests = db.relationship('ServiceRequest', back_populates='professional', cascade='all,delete',lazy=True)


# Services Table
class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.String, nullable=False)
    time = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text,nullable=False)
    professional = db.relationship('ServiceProfessional',cascade='all, delete', lazy=True, backref ='services')


# Service Requests Table
class ServiceRequest(db.Model):
    __tablename__ = "service_requests"
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professionals.id'), nullable=True)  # Can be null before assignment
    date_of_request = db.Column(db.DateTime, nullable=False)
    date_of_completion = db.Column(db.DateTime)
    service_status = db.Column(db.String(50))  # e.g., requested, confirmed, completed , rejected
    remarks = db.Column(db.String(255))
    reviews = db.Column(db.Integer, CheckConstraint('reviews>=0 AND reviews<=5'), default=None)
    service = db.relationship('Service', backref='service_requests')  # Link to Service model
    professional = db.relationship('ServiceProfessional', back_populates='sp_servicerequests')  # Link to ServiceProfessional model
    customer = db.relationship('Customer', back_populates='c_servicerequests')