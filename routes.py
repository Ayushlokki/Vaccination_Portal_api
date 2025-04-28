from flask import Blueprint, request, jsonify
from datetime import date, timedelta
from models import db, Student, VaccinationDrive, VaccinationRecord
from datetime import datetime

import csv
import io

bp = Blueprint("api", __name__, url_prefix="/api")

# Student CRUD
@bp.route("/students", methods=["GET"])
def get_students():
    students = Student.query.all()

    for s in students:
        student_data = {
            "id": s.id,
            "name": s.name,
            "class": s.student_class,
            "vaccine_name":s.vaccine_name,
            "vaccine_date":s.vaccination_date
        }
     
        return jsonify([{"id": s.id,
            "name": s.name,
            "class": s.student_class,
            "vaccine_name":s.vaccine_name,
            "vaccine_date":s.vaccination_date } for s in students])
    # students = Student.query.all()
    # for sd in students:
    #     print("data", vars(sd), flush=True)
    # return jsonify([{ "id": s.id, "name": s.name, "class": s.student_class, "roll": s.roll_number } for s in students])

# @bp.route("/students", methods=["POST"])
# def add_student():
#     data = request.json
#     new_student = Student(
#         name=data["name"],
#         student_class=data["class"],
#         roll_number=data["roll"]
#     )
#     db.session.add(new_student)
#     db.session.commit()
#     return jsonify({"message": "Student added"}), 201
@bp.route("/studentdata", methods=["POST"])
def add_vaccination_record():
    data = request.get_json()

    # Extract fields from request JSON
    # student_id = data.get("student_id")
    student_name = data.get("name")
    vaccination_status = data.get("vaccination_status")
    vaccine_name = data.get("vaccine_name")
    # drive_id = data.get("drive_id")
    vaccination_date = data.get("vaccination_date") 
    student_class = data.get("class")

    # Check required fields
    if not all([student_name,student_class,vaccination_status]):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if student exists
    #student = Student.query.filter_by(name=student_name)
    #if not student:
     #   return jsonify({"error": "Student not found"}), 404

    student = Student.query.filter_by(name=student_name, student_class=student_class).first()
    
    if not student:
        student = Student(
            name=student_name,
            student_class=student_class,
            vaccine_name=None,  
            vaccination_date=None
        )
        db.session.add(student)
        db.session.commit()  # Commit to create the new student
    print("data",vaccination_date,vaccine_name)

    if vaccination_status == "Yes":
        if not vaccine_name or not vaccination_date:
            return jsonify({"error": "Vaccine name and date required"}), 400

        if student.vaccine_name == vaccine_name:
            return jsonify({"error": "This vaccine already recorded for the student"}), 400
        if student.vaccination_date is not None and not student.vaccine_name:
            return jsonify({"error": "vaccine_name cannot be null if vaccination_date is set"}), 400


        try:
            student.vaccination_date = datetime.strptime(vaccination_date, "%Y-%m-%d").date()
            student.vaccine_name = vaccine_name
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        db.session.commit()
        return jsonify({"message": "Record hass been added succesfully"}), 200

    
    student.vaccine_name = None
    student.vaccination_date = None
    db.session.commit()
    return jsonify({"message": "Vaccination data cleared"}), 200
       
 
@bp.route('/vaccination_upload', methods=['POST'])
def bulk_vaccination_upload():
        # 1️⃣ Validate upload
        if 'file' not in request.files:
            return jsonify({"error": "CSV file is required"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # 2️⃣ Parse CSV
        try:
            stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
            reader = csv.DictReader(stream)
        except Exception as e:
            return jsonify({"error": f"Could not read CSV: {e}"}), 400

        # 3️⃣ Process each row
        results = []
        for row_num, row in enumerate(reader, start=1):
            name      = row.get('name')
            cls       = row.get('class')
            status    = row.get('vaccination_status')
            vaccine   = row.get('vaccine_name')
            vac_date  = row.get('vaccination_date')

            # Basic validation
            if not (name and cls and status):
                results.append({"row": row_num, "error": "Missing required fields"})
                continue

            # Find or create student
            student = Student.query.filter_by(name=name, student_class=cls).first()
            if not student:
                student = Student(name=name, student_class=cls)
                db.session.add(student)
                db.session.commit()  # commit so student.id exists

        # Apply vaccination logic
            if status.lower() == 'yes':
                if not (vaccine and vac_date):
                    results.append({"row": row_num, "error": "vaccine_name & vaccination_date are required when status is Yes"})
                    continue

                # prevent duplicate entry
                if student.vaccine_name == vaccine:
                    results.append({"row": row_num, "error": "This vaccine already recorded"})
                    continue

                # parse date
                try:
                    student.vaccination_date = datetime.strptime(vac_date, "%Y-%m-%d").date()
                    student.vaccine_name    = vaccine
                except ValueError:
                    results.append({"row": row_num, "error": "Invalid date format; use YYYY-MM-DD"})
                    continue

            else:
                # clear any existing vaccine info
                student.vaccine_name    = None
                student.vaccination_date = None

            db.session.commit()
            results.append({"row": row_num, "message": "OK"})

        return jsonify(results), 200
 
  

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

