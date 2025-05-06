from flask import Blueprint, request, jsonify
from datetime import date, timedelta
from models import db, Student, VaccinationDrive
from datetime import datetime

import csv
import io

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/students", methods=["GET"])
def get_students():
    students = Student.query.all()
    if not students:
        return jsonify({"message": "No students found", "data": []}), 200 

    return jsonify([
        {
        "id": s.id,
        "name": s.name,
        "class": s.student_class,
        "vaccinated": s.vaccination_status,
        "vaccine_name": s.vaccine_name,
        "vaccine_date": s.vaccination_date.strftime("%Y-%m-%d") if s.vaccination_date else None
        
        }
        for s in students
    ])
@bp.route("/studentdata", methods=["POST"])
def add_vaccination_record():
    data = request.get_json()
    student_name = data.get("name")
    vaccination_status = data.get("vaccination_status")
    vaccine_name = data.get("vaccine_name")

    vaccination_date = data.get("vaccination_date") 
    student_class = data.get("class")

    if not all([student_name,student_class,vaccination_status]):
        return jsonify({"error": "Missing required fields"}), 400

    student = Student.query.filter_by(name=student_name, student_class=student_class).first()
    
    if not student:
        student = Student(
            name=student_name,
            student_class=student_class,
            vaccine_name=None,  
            vaccination_date=None,
            vaccination_status = vaccination_status
        )
        db.session.add(student)
        db.session.commit()
    print("data",vaccination_date,vaccine_name)

    if vaccination_status == "yes":
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
        if 'file' not in request.files:
            return jsonify({"error": "CSV file is required"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        try:
            stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
            reader = csv.DictReader(stream)
        except Exception as e:
            return jsonify({"error": f"Could not read CSV: {e}"}), 400

        results = []
        for row_num, row in enumerate(reader, start=1):
            name      = row.get('name')
            cls       = row.get('class')
            status    = row.get('vaccination_status')
            vaccine   = row.get('vaccine_name')
            vac_date  = row.get('vaccination_date')

            if not (name and cls and status):
                results.append({"row": row_num, "error": "Missing required fields"})
                continue
            print("status.lower()",vac_date)

            student = Student.query.filter_by(name=name, student_class=cls).first()
            if not student:
                student = Student(name=name, student_class=cls,vaccination_status=status.lower())
                db.session.add(student)
                db.session.commit() 

            if status.lower() == 'yes':
                if not (vaccine and vac_date):
                    results.append({"row": row_num, "error": "vaccine_name & vaccination_date are required when status is Yes"})
                    continue
                if student.vaccine_name == vaccine:
                    results.append({"row": row_num, "error": "This vaccine already recorded"})
                    continue
                try:
                    student.vaccination_date = datetime.strptime(vac_date, "%Y-%m-%d").date()
                    student.vaccine_name    = vaccine
                    student.vaccination_status = 'yes' 
                except ValueError:
                    results.append({"row": row_num, "error": "Invalid date format; use YYYY-MM-DD"})
                    continue

            else:
                student.vaccine_name    = None
                student.vaccination_date = None
                student.vaccination_status = 'no' 

            db.session.commit()
            results.append({"row": row_num, "message": "OK"})

        return jsonify({
            "message": "Data Added Successfully",
            "data": results
        }), 200
 
  
@bp.route("/adddrives", methods=["POST"])
def create_drive():
    print("dtart")
    data = request.get_json()
    print("DEBUG - Received JSON:", data) 
    drive_date = datetime.strptime(data.get("drive_date"),"%Y-%m-%d").date()
    if drive_date < date.today() + timedelta(days=15):
        return jsonify({"error": "Drives must be scheduled at least 15 days in advance"}), 400

    existing_drive = VaccinationDrive.query.filter_by(vaccination_date=drive_date).first()
    if existing_drive:
        return jsonify({"error": "Drive already scheduled on this date"}), 400

    drive = VaccinationDrive(
        vaccine_name=data.get("vaccine_name"),
        vaccination_date=drive_date,
        available_doses=data.get("available_doses"),
        applicable_classes=data.get("applicable_classes")
    )
    db.session.add(drive)
    db.session.commit()
    return jsonify({"message": "Drive created"})

@bp.route("/drives/<int:id>", methods=["PUT"])
def update_drive(id):
    data = request.json
    new_drive_date = datetime.strptime(data["drive_date"], "%Y-%m-%d").date()

    if new_drive_date < date.today() + timedelta(days=15):
        return jsonify({"error": "Drives must be scheduled at least 15 days in advance"}), 400

    drive = VaccinationDrive.query.get_or_404(id)

    if drive.vaccination_date != new_drive_date:
        existing_drive = VaccinationDrive.query.filter_by(vaccination_date=new_drive_date).first()
        if existing_drive:
            return jsonify({"error": "Another drive is already scheduled on this date"}), 400

    drive.vaccine_name = data["vaccine_name"]
    drive.vaccination_date = new_drive_date
    drive.available_doses = data["available_doses"]
    drive.applicable_classes = data["applicable_classes"]

    db.session.commit()
    return jsonify({"message": "Drive updated"})

@bp.route("/drives", methods=["GET"])
def getDrives():
    driveData = VaccinationDrive.query.all()
    return jsonify([{"id": s.id,
            "applicable_classes": s.applicable_classes,
            "vaccine_name":s.vaccine_name,
            "drive_date":s.vaccination_date.strftime("%Y-%m-%d"),
            "available_doses":s.available_doses} for s in driveData])
    
    
    
    
@bp.route('/reports/vaccinations', methods=['GET'])
def get_vaccination_report():
    vaccine_name = request.args.get('vaccine_name', '').strip()

    try:
        if vaccine_name:
            students = Student.query.filter(Student.vaccine_name == vaccine_name).all()
        else:
            students = Student.query.all()

        result = []
        for student in students:
            result.append({
                'student_name': student.name,
                'vaccinated': student.vaccination_status,
                'vaccination_date': student.vaccination_date.isoformat() if student.vaccination_date else None,
                'vaccine_name': student.vaccine_name or ''
            })

        return jsonify(result), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Failed to fetch report'}), 500


@bp.route("/metrics", methods=["GET"])
def get_metrics():
    total_students = Student.query.count()
    vaccinated = Student.query.filter_by(vaccination_status="yes").count()
    drives = VaccinationDrive.query.filter(
    VaccinationDrive.vaccination_date >= date.today(),
    VaccinationDrive.vaccination_date <= date.today() + timedelta(days=30)
    ).all()
    drive_list = [{"name": d.vaccine_name, "date": d.vaccination_date.isoformat()} for d in drives]
    return jsonify({
        "total_students": total_students,
        "vaccinated_count": vaccinated,
        "vaccinated_percent": round((vaccinated / total_students) * 100 if total_students > 0 else 0, 2),
        "upcoming_drives": drive_list
    })

