
import os
import sys
from flask import Flask, render_template, request, jsonify, send_file

# Ensure local imports work cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hospital_manager import HospitalManager

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["JSON_SORT_KEYS"] = False

# Initialize the central Hospital Manager instance
manager = HospitalManager()

# Automatically seed realistic sample cases on startup so the UI is immediately alive
manager.seed_sample_data()


@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("index.html")


@app.route("/download-zip")
def download_zip():
    """Download the complete hospital emergency management system ZIP archive."""
    zip_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hospital_emergency_system.zip"))
    if not os.path.exists(zip_path):
        zip_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "hospital_emergency_system.zip"))
    return send_file(zip_path, as_attachment=True, download_name="hospital_emergency_system.zip")


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    """Get real-time dashboard statistics and active bay states."""
    try:
        summary = manager.get_dashboard_summary()
        return jsonify({"success": True, "data": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/queue", methods=["GET"])
def get_queue():
    """Get the current live queue ordered by Emergency Priority and arrival FIFO."""
    try:
        ordered_queue = manager.emergency_queue.get_ordered_list()
        return jsonify({
            "success": True,
            "count": len(ordered_queue),
            "queue": ordered_queue
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/queue/call-next", methods=["POST"])
def call_next():
    """Call the highest-priority patient waiting into an available ER bay."""
    try:
        payload = request.get_json(silent=True) or {}
        bay_id = payload.get("bay_id")
        doctor = payload.get("doctor")
        
        result = manager.call_next_patient(bay_id=bay_id, doctor_name=doctor)
        if not result:
            return jsonify({"success": False, "message": "No patients currently waiting in the emergency queue."}), 400
            
        return jsonify({
            "success": True,
            "message": f"Patient {result['patient']['name']} ({result['patient']['patient_id']}) admitted to {result['bay']['name']}!",
            "data": result
        })
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/queue/admit", methods=["POST"])
def admit_patient():
    """Directly admit a specific patient from queue to an available bay."""
    try:
        payload = request.get_json() or {}
        patient_id = payload.get("patient_id")
        bay_id = payload.get("bay_id")
        doctor = payload.get("doctor")

        if not patient_id:
            return jsonify({"success": False, "message": "patient_id is required."}), 400

        result = manager.admit_specific_patient(patient_id, bay_id=bay_id, doctor_name=doctor)
        return jsonify({
            "success": True,
            "message": f"Patient {result['patient']['name']} admitted to {result['bay']['name']}.",
            "data": result
        })
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/patients/register", methods=["POST"])
def register_patient():
    """
    Register a patient:
    - Appends to dynamic Doubly Linked List
    - Enqueues into Priority Queue (Emergency first, Normal FIFO)
    """
    try:
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        age = data.get("age")
        gender = data.get("gender", "Other")
        contact = data.get("contact", "").strip()
        blood_group = data.get("blood_group", "Unknown")
        chief_complaint = data.get("chief_complaint", "").strip()
        priority = int(data.get("priority", 4))
        notes = data.get("notes", "").strip()

        if not name or not age or not chief_complaint:
            return jsonify({"success": False, "message": "Name, age, and chief complaint are required."}), 400

        vitals = {
            "heart_rate": int(data.get("heart_rate", 80) or 80),
            "blood_pressure": data.get("blood_pressure", "120/80") or "120/80",
            "spo2": int(data.get("spo2", 98) or 98),
            "temperature": float(data.get("temperature", 98.6) or 98.6)
        }

        patient = manager.register_patient(
            name=name,
            age=int(age),
            gender=gender,
            contact=contact,
            blood_group=blood_group,
            chief_complaint=chief_complaint,
            priority=priority,
            vitals=vitals,
            notes=notes
        )

        return jsonify({
            "success": True,
            "message": f"Patient {patient.name} registered successfully with ID {patient.patient_id}!",
            "patient": patient.to_dict()
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/patients", methods=["GET"])
def get_all_patients():
    """
    Traverse the dynamic Linked List to return patient records.
    Supports filtering by search query, status, and priority.
    """
    try:
        search_query = request.args.get("search", "").lower().strip()
        status_filter = request.args.get("status", "").lower().strip()
        priority_filter = request.args.get("priority", "").strip()

        records = manager.patient_records.to_list()

        # Apply filters
        if search_query:
            records = [
                r for r in records
                if search_query in r["patient_id"].lower()
                or search_query in r["name"].lower()
                or search_query in r["chief_complaint"].lower()
            ]

        if status_filter and status_filter != "all":
            records = [r for r in records if r["status"].lower() == status_filter]

        if priority_filter and priority_filter != "all":
            try:
                p_int = int(priority_filter)
                records = [r for r in records if r["priority"] == p_int]
            except ValueError:
                pass

        return jsonify({
            "success": True,
            "total_records": len(records),
            "records": records
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/patients/<patient_id>", methods=["GET"])
def get_patient(patient_id):
    """Retrieve single patient record from linked list."""
    try:
        patient = manager.patient_records.find(patient_id)
        if not patient:
            return jsonify({"success": False, "message": "Patient not found."}), 404
        return jsonify({"success": True, "patient": patient.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/patients/<patient_id>", methods=["PUT"])
def update_patient(patient_id):
    """Update patient details dynamically in the linked list."""
    try:
        data = request.get_json() or {}
        patient = manager.patient_records.find(patient_id)
        if not patient:
            return jsonify({"success": False, "message": "Patient not found."}), 404

        if "name" in data: patient.name = data["name"]
        if "age" in data: patient.age = int(data["age"])
        if "gender" in data: patient.gender = data["gender"]
        if "contact" in data: patient.contact = data["contact"]
        if "blood_group" in data: patient.blood_group = data["blood_group"]
        if "chief_complaint" in data: patient.chief_complaint = data["chief_complaint"]
        if "notes" in data: patient.notes = data["notes"]
        if "vitals" in data and isinstance(data["vitals"], dict):
            patient.vitals.update(data["vitals"])

        return jsonify({"success": True, "message": "Patient record updated.", "patient": patient.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/patients/<patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    """Delete a patient record from linked list, queue, and treatment bays."""
    try:
        # Remove from queue if waiting
        manager.emergency_queue.remove(patient_id)
        
        # Free bay if occupied
        for b in manager.bays:
            if b["patient_id"] == patient_id:
                b["patient_id"] = None

        # Delete from linked list
        deleted = manager.patient_records.delete(patient_id)
        if not deleted:
            return jsonify({"success": False, "message": "Patient record not found."}), 404

        return jsonify({"success": True, "message": f"Patient {patient_id} record deleted from system."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/patients/re-triage", methods=["POST"])
def re_triage():
    """Change triage priority for a waiting patient (e.g. condition deteriorated)."""
    try:
        data = request.get_json() or {}
        patient_id = data.get("patient_id")
        new_priority = int(data.get("priority", 4))
        reason = data.get("reason", "").strip()

        if not patient_id:
            return jsonify({"success": False, "message": "patient_id is required."}), 400

        success = manager.re_triage(patient_id, new_priority, reason)
        if not success:
            return jsonify({"success": False, "message": "Could not re-triage patient."}), 400

        return jsonify({
            "success": True,
            "message": f"Patient {patient_id} priority updated to Priority {new_priority}!"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/treatment/complete", methods=["POST"])
def complete_treatment():
    """Mark treatment completed for a patient in a bay, log notes, and discharge."""
    try:
        data = request.get_json() or {}
        patient_id = data.get("patient_id")
        diagnosis = data.get("diagnosis", "").strip()
        medications = data.get("medications", "").strip()
        outcome = data.get("outcome", "Discharged")
        doctor_notes = data.get("notes", "").strip()

        if not patient_id:
            return jsonify({"success": False, "message": "patient_id is required."}), 400
        if not diagnosis:
            return jsonify({"success": False, "message": "Clinical diagnosis is required."}), 400

        patient = manager.complete_treatment(
            patient_id=patient_id,
            diagnosis=diagnosis,
            medications=medications,
            outcome=outcome,
            doctor_notes=doctor_notes
        )

        return jsonify({
            "success": True,
            "message": f"Treatment completed for {patient.name}. Status marked as Discharged/Completed.",
            "patient": patient.to_dict()
        })
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/linked-list/debug", methods=["GET"])
def get_linked_list_graph():
    """
    Returns visual representation of the dynamic Doubly Linked List
    showing actual nodes, prev/next pointers, and data payload.
    """
    try:
        graph = manager.patient_records.to_visual_graph()
        return jsonify({"success": True, "data": graph})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/demo/seed", methods=["POST"])
def seed_demo():
    """Reset and seed rich sample data for demonstration."""
    try:
        manager.seed_sample_data()
        return jsonify({"success": True, "message": "Emergency system re-seeded with sample clinical cases!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/demo/reset", methods=["POST"])
def reset_all():
    """Reset all records, queues, and beds."""
    try:
        manager.reset_all()
        return jsonify({"success": True, "message": "All records and queues have been cleared."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Hospital Emergency Management System starting at http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
