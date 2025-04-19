from flask import Blueprint, request, jsonify
from datetime import date, timedelta
from models import db, Student, VaccinationDrive, VaccinationRecord

bp = Blueprint("api", __name__, url_prefix="/api")

# Simulated login
@bp.route("/login", methods=["POST"])
def login():
    return jsonify({"token": "fake-token", "user": "admin"})

# Student CRUD
@bp.route("/students", methods=["GET"])
def get_students():
    students = Student.query.all()
    return jsonify([{ "id": s.id, "name": s.name, "class": s.student_class, "roll": s.roll_number } for s in students])

@bp.route("/students", methods=["POST"])
def add_student():
    data = request.json
    new_student = Student(
        name=data["name"],
        student_class=data["class"],
        roll_number=data["roll"]
    )
    db.session.add(new_student)
    db.session.commit()
    return jsonify({"message": "Student added"}), 201

# Vaccination Drive
@bp.route("/drives", methods=["POST"])
def create_drive():
    data = request.json
    drive_date = date.fromisoformat(data["drive_date"])
    if drive_date < date.today() + timedelta(days=15):
        return jsonify({"error": "Drives must be scheduled at least 15 days in advance"}), 400

    existing_drive = VaccinationDrive.query.filter_by(drive_date=drive_date).first()
    if existing_drive:
        return jsonify({"error": "Drive already scheduled on this date"}), 400

    drive = VaccinationDrive(
        vaccine_name=data["vaccine_name"],
        drive_date=drive_date,
        available_doses=data["available_doses"],
        applicable_classes=','.join(data["applicable_classes"])
    )
    db.session.add(drive)
    db.session.commit()
    return jsonify({"message": "Drive created"})

# Dashboard Metrics
@bp.route("/metrics", methods=["GET"])
def get_metrics():
    total_students = Student.query.count()
    vaccinated = VaccinationRecord.query.count()
    upcoming_drives = VaccinationDrive.query.filter(
        VaccinationDrive.drive_date >= date.today(),
        VaccinationDrive.drive_date <= date.today() + timedelta(days=30)
    ).count()
    return jsonify({
        "total_students": total_students,
        "vaccinated_count": vaccinated,
        "vaccinated_percent": round((vaccinated / total_students) * 100 if total_students > 0 else 0, 2),
        "upcoming_drives": upcoming_drives
    })

