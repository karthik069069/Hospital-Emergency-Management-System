"""Integration test suite for Flask Hospital Emergency System API."""

import sys
import os
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, manager


class TestHospitalAPI(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        manager.seed_sample_data()

    def test_dashboard_endpoint(self):
        """Test GET /api/dashboard returns correct status and counts."""
        res = self.client.get('/api/dashboard')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("waiting_in_queue", data["data"])
        self.assertIn("bays", data["data"])

    def test_queue_ordering_emergency_first(self):
        """Test GET /api/queue maintains emergency before normal cases."""
        res = self.client.get('/api/queue')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        queue = data["queue"]
        
        # Verify that all P1 cases come before P2, P2 before P3, P3 before P4
        priorities = [p["priority"] for p in queue]
        self.assertEqual(priorities, sorted(priorities), "Queue must be strictly ordered by priority (P1 < P2 < P3 < P4)!")

    def test_patient_registration_and_linked_list(self):
        """Test registering a patient inserts into linked list and queue."""
        initial_nodes = len(manager.patient_records)
        
        payload = {
            "name": "David Copperfield",
            "age": 48,
            "gender": "Male",
            "contact": "555-9999",
            "blood_group": "B-",
            "chief_complaint": "Severe chest tightness and pale skin",
            "priority": 1,
            "heart_rate": 110,
            "blood_pressure": "160/95",
            "spo2": 89,
            "temperature": 98.4,
            "notes": "Emergency code 1"
        }
        res = self.client.post('/api/patients/register', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        patient_id = data["patient"]["patient_id"]

        # Verify dynamic linked list grew
        self.assertEqual(len(manager.patient_records), initial_nodes + 1)
        
        # Verify patient is in linked list
        node = manager.patient_records.find_node(patient_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.patient.name, "David Copperfield")

        # Because priority is 1, they should be at the FRONT of queue (or after existing P1s)
        next_in_line = manager.emergency_queue.peek()
        self.assertEqual(next_in_line.priority, 1)

    def test_call_next_and_treatment_flow(self):
        """Test calling next patient into an ER bed, then completing treatment."""
        # Call next patient
        res = self.client.post('/api/queue/call-next')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        patient_id = data["data"]["patient"]["patient_id"]
        bay_id = data["data"]["bay"]["id"]

        # Verify patient is now under treatment
        p_record = manager.patient_records.find(patient_id)
        self.assertEqual(p_record.status, "under_treatment")

        # Complete treatment
        completion_payload = {
            "patient_id": patient_id,
            "diagnosis": "Acute Bronchospasm resolved with nebulization",
            "medications": "Salbutamol 5mg Neb, Prednisolone 40mg",
            "outcome": "Discharged Home",
            "notes": "Patient condition stabilized. Follow up with GP in 3 days."
        }
        res_comp = self.client.post('/api/treatment/complete', data=json.dumps(completion_payload), content_type='application/json')
        self.assertEqual(res_comp.status_code, 200)
        comp_data = res_comp.get_json()
        self.assertTrue(comp_data["success"])

        # Patient record is now completed, and bed is freed
        self.assertEqual(p_record.status, "completed")
        freed_bay = next(b for b in manager.bays if b["id"] == bay_id)
        self.assertIsNone(freed_bay["patient_id"], "Bay must be vacant after treatment completion!")

    def test_linked_list_visual_debug(self):
        """Test GET /api/linked-list/debug returns linked pointers."""
        res = self.client.get('/api/linked-list/debug')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        graph = data["data"]
        self.assertIn("head_id", graph)
        self.assertIn("tail_id", graph)
        self.assertTrue(len(graph["nodes"]) > 0)
        # Check node pointer integrity
        first_node = graph["nodes"][0]
        self.assertIsNone(first_node["prev_id"])
        self.assertIsNotNone(first_node["next_id"])


if __name__ == '__main__':
    unittest.main()
