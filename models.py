from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_class = db.Column(db.String(50), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    vaccination_records = db.relationship("VaccinationRecord", backref="student")

class VaccinationDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vaccine_name = db.Column(db.String(100), nullable=False)
    drive_date = db.Column(db.Date, nullable=False)
    available_doses = db.Column(db.Integer, nullable=False)
    applicable_classes = db.Column(db.String(200))

class VaccinationRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("vaccination_drive.id"), nullable=False)
    vaccination_date = db.Column(db.Date, default=date.today)