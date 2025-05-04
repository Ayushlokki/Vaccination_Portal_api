from flask_sqlalchemy import SQLAlchemy
from datetime import date
from sqlalchemy.orm import validates

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_class = db.Column(db.String(50), nullable=False)
    vaccination_status = db.Column(db.String(50), nullable=False)
    vaccine_name = db.Column(db.String(50), nullable=True)
    vaccination_date = db.Column(db.Date, nullable=True)
   


class VaccinationDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vaccine_name = db.Column(db.String(100), nullable=False)
    vaccination_date = db.Column(db.Date, unique=True, nullable=False)
    available_doses = db.Column(db.Integer, nullable=False)
    applicable_classes = db.Column(db.String(200))
