"""
Hospital Manager Service
Orchestrates patient registration, priority triage, queue operations,
treatment bay allocation, and record maintenance via the linked list.
"""

from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional, Any

from data_structures import Patient, PatientLinkedList, EmergencyPriorityQueue


class HospitalManager:
    """Central controller for the Hospital Emergency Management System."""
    
    # Available Treatment Bays in the Emergency Department
    DEFAULT_BAYS = [
        {"id": "BAY-1", "name": "Trauma & Resuscitation 1", "type": "Critical Care", "patient_id": None},
        {"id": "BAY-2", "name": "Acute Emergency 2", "type": "Acute Care", "patient_id": None},
        {"id": "BED-3", "name": "Urgent Care Bed 3", "type": "Urgent Care", "patient_id": None},
        {"id": "BED-4", "name": "General ER Bed 4", "type": "General Observation", "patient_id": None},
        {"id": "BED-5", "name": "Fast-Track Bed 5", "type": "Rapid Assessment", "patient_id": None},
        {"id": "ROOM-6", "name": "Consultation Room 6", "type": "Outpatient / Minor", "patient_id": None},
    ]

    DOCTORS = [
        "Dr. Sarah Jenkins (ER Attending)",
        "Dr. Marcus Vance (Trauma Surgeon)",
        "Dr. Priya Sharma (Emergency Physician)",
        "Dr. Elena Rostova (Critical Care Specialist)",
        "Dr. David Kim (Senior Resident)"
    ]

    def __init__(self):
        self.patient_records = PatientLinkedList()
        self.emergency_queue = EmergencyPriorityQueue()
        self.bays = [dict(b) for b in self.DEFAULT_BAYS]
        self._next_id_counter = 101

    def _generate_id(self) -> str:
        pid = f"EMG-{self._next_id_counter}"
        self._next_id_counter += 1
        return pid

    def register_patient(
        self,
        name: str,
        age: int,
        gender: str,
        contact: str,
        blood_group: str,
        chief_complaint: str,
        priority: int = 4,
        vitals: Optional[Dict[str, Any]] = None,
        notes: str = ""
    ) -> Patient:
        """
        Register a new patient into the system:
        1. Allocates unique patient ID.
        2. Dynamically creates a node and appends it to PatientLinkedList.
        3. Enqueues the patient into EmergencyPriorityQueue.
        """
        patient_id = self._generate_id()
        patient = Patient(
            patient_id=patient_id,
            name=name,
            age=age,
            gender=gender,
            contact=contact,
            blood_group=blood_group,
            chief_complaint=chief_complaint,
            priority=priority,
            vitals=vitals,
            notes=notes
        )

        # 1. Store dynamically in Linked List
        self.patient_records.append(patient)

        # 2. Add to Priority Queue
        self.emergency_queue.enqueue(patient)

        return patient

    def call_next_patient(self, bay_id: Optional[str] = None, doctor_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Calls the highest-priority patient waiting in the queue (or FIFO for normal cases):
        1. Pops next patient from EmergencyPriorityQueue.
        2. Assigns to an available treatment bay.
        3. Updates patient record in the Linked List to 'under_treatment'.
        """
        if self.emergency_queue.is_empty:
            return None

        # Find an available bay
        assigned_bay = None
        if bay_id:
            assigned_bay = next((b for b in self.bays if b["id"] == bay_id and b["patient_id"] is None), None)
        
        if not assigned_bay:
            assigned_bay = next((b for b in self.bays if b["patient_id"] is None), None)

        if not assigned_bay:
            raise ValueError("All Emergency Treatment Bays are currently occupied! Please complete treatment on an occupied bed first.")

        # Dequeue patient based on Emergency Priority (P1 > P2 > P3 > P4) and FIFO within priority
        patient = self.emergency_queue.dequeue()
        if not patient:
            return None

        # Assign bay & doctor
        doctor = doctor_name or random.choice(self.DOCTORS)
        assigned_bay["patient_id"] = patient.patient_id

        # Update patient status in linked list
        patient.status = "under_treatment"
        patient.treatment["doctor"] = doctor
        patient.treatment["bay_or_bed"] = f"{assigned_bay['id']} - {assigned_bay['name']}"
        patient.treatment["started_at"] = datetime.now().isoformat()

        return {
            "patient": patient.to_dict(),
            "bay": assigned_bay
        }

    def admit_specific_patient(self, patient_id: str, bay_id: Optional[str] = None, doctor_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Admit a specific patient directly from the queue to a bay."""
        assigned_bay = None
        if bay_id:
            assigned_bay = next((b for b in self.bays if b["id"] == bay_id and b["patient_id"] is None), None)
        if not assigned_bay:
            assigned_bay = next((b for b in self.bays if b["patient_id"] is None), None)

        if not assigned_bay:
            raise ValueError("No treatment bays available.")

        patient = self.emergency_queue.remove(patient_id)
        if not patient:
            # Maybe already in linked list
            patient = self.patient_records.find(patient_id)
            if not patient or patient.status != "waiting":
                raise ValueError("Patient is not waiting in the queue.")

        doctor = doctor_name or random.choice(self.DOCTORS)
        assigned_bay["patient_id"] = patient.patient_id

        patient.status = "under_treatment"
        patient.treatment["doctor"] = doctor
        patient.treatment["bay_or_bed"] = f"{assigned_bay['id']} - {assigned_bay['name']}"
        patient.treatment["started_at"] = datetime.now().isoformat()

        return {
            "patient": patient.to_dict(),
            "bay": assigned_bay
        }

    def complete_treatment(
        self,
        patient_id: str,
        diagnosis: str,
        medications: str,
        outcome: str,
        doctor_notes: str = ""
    ) -> Optional[Patient]:
        """
        Completes treatment for a patient:
        1. Records diagnosis, medications, outcome, and timestamp in linked list record.
        2. Sets status to 'completed'.
        3. Frees the assigned bay/bed.
        """
        patient = self.patient_records.find(patient_id)
        if not patient:
            raise ValueError(f"Patient with ID {patient_id} not found in records.")

        if patient.status != "under_treatment":
            raise ValueError(f"Patient {patient_id} is not currently under treatment.")

        # Complete treatment details
        patient.treatment["completed_at"] = datetime.now().isoformat()
        patient.treatment["diagnosis"] = diagnosis
        patient.treatment["medications"] = medications
        patient.treatment["outcome"] = outcome
        if doctor_notes:
            patient.notes = f"{patient.notes} | Doctor Note: {doctor_notes}".strip(" | ")

        patient.status = "completed"

        # Free the bay
        for b in self.bays:
            if b["patient_id"] == patient_id:
                b["patient_id"] = None

        return patient

    def re_triage(self, patient_id: str, new_priority: int, reason: str = "") -> bool:
        """
        Escalates or changes patient priority when clinical condition changes.
        Updates both the linked list record and priority queue ordering.
        """
        patient = self.patient_records.find(patient_id)
        if not patient:
            return False

        old_p = patient.priority
        patient.priority = new_priority
        if reason:
            patient.notes = f"{patient.notes} [Re-triaged from P{old_p} to P{new_priority}: {reason}]".strip()

        # Update queue position
        if patient.status == "waiting":
            self.emergency_queue.re_triage(patient_id, new_priority)

        return True

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Returns comprehensive real-time statistics for the hospital dashboard."""
        all_patients = self.patient_records.to_list()
        
        waiting_count = len(self.emergency_queue)
        in_treatment_count = sum(1 for b in self.bays if b["patient_id"] is not None)
        completed_count = sum(1 for p in all_patients if p["status"] == "completed")
        
        queue_by_priority = self.emergency_queue.count_by_priority()
        
        # Treatment bays with attached patient summaries
        bays_info = []
        for bay in self.bays:
            b_info = dict(bay)
            if bay["patient_id"]:
                p = self.patient_records.find(bay["patient_id"])
                b_info["patient"] = p.to_dict() if p else None
            else:
                b_info["patient"] = None
            bays_info.append(b_info)

        return {
            "total_registered": len(self.patient_records),
            "waiting_in_queue": waiting_count,
            "under_treatment": in_treatment_count,
            "completed": completed_count,
            "critical_cases_waiting": queue_by_priority.get(1, 0),
            "queue_by_priority": queue_by_priority,
            "available_bays": len(self.bays) - in_treatment_count,
            "total_bays": len(self.bays),
            "bays": bays_info,
            "next_in_line": self.emergency_queue.peek().to_dict() if self.emergency_queue.peek() else None
        }

    def seed_sample_data(self):
        """Populates rich demo data with emergency and normal cases for immediate testing."""
        self.reset_all()

        samples = [
            # Normal Cases (Arrived earlier)
            {
                "name": "Evelyn Reed", "age": 29, "gender": "Female", "contact": "+1-555-0142",
                "blood_group": "A+", "chief_complaint": "Persistent mild fever and sore throat for 3 days",
                "priority": 4, "vitals": {"heart_rate": 78, "blood_pressure": "118/76", "spo2": 99, "temperature": 99.8},
                "notes": "No known allergies. Took paracetamol at home."
            },
            {
                "name": "Liam Gallagher", "age": 34, "gender": "Male", "contact": "+1-555-0189",
                "blood_group": "O+", "chief_complaint": "Twisted right ankle during morning jogging, mild swelling",
                "priority": 4, "vitals": {"heart_rate": 72, "blood_pressure": "122/80", "spo2": 98, "temperature": 98.4},
                "notes": "Able to bear partial weight. RICE protocol initiated."
            },
            # Semi-Urgent Case
            {
                "name": "Sofia Hernandez", "age": 42, "gender": "Female", "contact": "+1-555-0271",
                "blood_group": "B+", "chief_complaint": "Deep cut on palm from broken kitchen glass, active bleeding controlled with pressure",
                "priority": 3, "vitals": {"heart_rate": 86, "blood_pressure": "128/82", "spo2": 99, "temperature": 98.6},
                "notes": "Tetanus booster received 2 years ago. Needs sutures."
            },
            # Emergency Case (Arrived after normal cases!)
            {
                "name": "Arthur Pendelton", "age": 67, "gender": "Male", "contact": "+1-555-0394",
                "blood_group": "O-", "chief_complaint": "Sudden crushing retrosternal chest pain radiating to left jaw, diaphoresis",
                "priority": 1, "vitals": {"heart_rate": 115, "blood_pressure": "175/105", "spo2": 91, "temperature": 98.2},
                "notes": "History of hypertension and coronary artery disease. Emergency Code Crimson."
            },
            # Urgent Case
            {
                "name": "Maya Lin", "age": 19, "gender": "Female", "contact": "+1-555-0422",
                "blood_group": "AB+", "chief_complaint": "Acute severe asthma exacerbation, wheezing and audible stridor",
                "priority": 2, "vitals": {"heart_rate": 108, "blood_pressure": "130/85", "spo2": 92, "temperature": 98.9},
                "notes": "Albuterol inhaler used 3 times without relief."
            },
            # Another Normal Case
            {
                "name": "Oliver Twist", "age": 22, "gender": "Male", "contact": "+1-555-0511",
                "blood_group": "A-", "chief_complaint": "Mild stomach ache after meal, no vomiting",
                "priority": 4, "vitals": {"heart_rate": 75, "blood_pressure": "115/75", "spo2": 99, "temperature": 98.6},
                "notes": "No previous medical issues."
            }
        ]

        # Register all samples
        for s in samples:
            self.register_patient(
                name=s["name"],
                age=s["age"],
                gender=s["gender"],
                contact=s["contact"],
                blood_group=s["blood_group"],
                chief_complaint=s["chief_complaint"],
                priority=s["priority"],
                vitals=s["vitals"],
                notes=s["notes"]
            )

        # Call the first emergency patient into Bay 1 to show active treatment
        self.call_next_patient(bay_id="BAY-1", doctor_name="Dr. Sarah Jenkins (ER Attending)")

    def reset_all(self):
        """Clears all records, queues, and treatment bays."""
        self.patient_records.clear()
        self.emergency_queue.clear()
        for b in self.bays:
            b["patient_id"] = None
        self._next_id_counter = 101
