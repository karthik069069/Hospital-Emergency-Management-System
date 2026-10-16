"""Unit tests for Patient, PatientLinkedList, and EmergencyPriorityQueue."""

import sys
import os
import unittest
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_structures import Patient, PatientLinkedList, EmergencyPriorityQueue


class TestHospitalDataStructures(unittest.TestCase):

    def setUp(self):
        self.ll = PatientLinkedList()
        self.pq = EmergencyPriorityQueue()

    def test_linked_list_operations(self):
        """Test dynamic insertion, node linking, search, update, and deletion in linked list."""
        p1 = Patient("P-101", "John Doe", 45, "Male", "555-0101", "O+", "Chest Pain", priority=1)
        p2 = Patient("P-102", "Jane Smith", 32, "Female", "555-0102", "A+", "Mild Fever", priority=4)
        p3 = Patient("P-103", "Bob Wilson", 60, "Male", "555-0103", "B+", "Fracture", priority=2)

        # 1. Dynamic append
        n1 = self.ll.append(p1)
        n2 = self.ll.append(p2)
        n3 = self.ll.append(p3)

        self.assertEqual(len(self.ll), 3)
        self.assertEqual(self.ll.head.patient.patient_id, "P-101")
        self.assertEqual(self.ll.tail.patient.patient_id, "P-103")

        # Verify doubly linked pointers
        self.assertIsNone(n1.prev)
        self.assertEqual(n1.next, n2)
        self.assertEqual(n2.prev, n1)
        self.assertEqual(n2.next, n3)
        self.assertEqual(n3.prev, n2)
        self.assertIsNone(n3.next)

        # 2. Search
        found = self.ll.find("P-102")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Jane Smith")

        # 3. Update
        updated = self.ll.update("P-102", notes="Allergic to penicillin", chief_complaint="High Fever")
        self.assertTrue(updated)
        self.assertEqual(self.ll.find("P-102").notes, "Allergic to penicillin")
        self.assertEqual(self.ll.find("P-102").chief_complaint, "High Fever")

        # 4. Traversal
        record_list = self.ll.to_list()
        self.assertEqual(len(record_list), 3)
        self.assertEqual([r["patient_id"] for r in record_list], ["P-101", "P-102", "P-103"])

        # 5. Delete middle node
        deleted = self.ll.delete("P-102")
        self.assertTrue(deleted)
        self.assertEqual(len(self.ll), 2)
        self.assertIsNone(self.ll.find("P-102"))
        self.assertEqual(n1.next, n3)
        self.assertEqual(n3.prev, n1)

        # 6. Delete head
        self.ll.delete("P-101")
        self.assertEqual(self.ll.head.patient.patient_id, "P-103")
        self.assertEqual(len(self.ll), 1)

        # 7. Delete tail
        self.ll.delete("P-103")
        self.assertTrue(self.ll.is_empty)
        self.assertIsNone(self.ll.head)
        self.assertIsNone(self.ll.tail)

    def test_priority_queue_emergency_first(self):
        """Test that emergency cases are served first, before normal FIFO cases."""
        # Normal cases arrive first
        norm1 = Patient("N-01", "Normal 1", 30, "Male", "555-1", "O+", "Mild Cold", priority=4)
        norm2 = Patient("N-02", "Normal 2", 28, "Female", "555-2", "A+", "Sprained Ankle", priority=4)
        
        self.pq.enqueue(norm1)
        self.pq.enqueue(norm2)

        # Later, an emergency case arrives!
        emerg1 = Patient("E-01", "Emergency 1", 55, "Male", "555-3", "B+", "Cardiac Arrest", priority=1)
        self.pq.enqueue(emerg1)

        # Another urgent case arrives
        urg1 = Patient("U-01", "Urgent 1", 40, "Female", "555-4", "AB+", "Deep Cut", priority=3)
        self.pq.enqueue(urg1)

        # Even though emerg1 arrived third, it MUST be dequeued FIRST!
        next_up = self.pq.dequeue()
        self.assertEqual(next_up.patient_id, "E-01", "Emergency priority 1 must be served first!")

        # Next should be Urgent 1 (Priority 3)
        next_up2 = self.pq.dequeue()
        self.assertEqual(next_up2.patient_id, "U-01", "Priority 3 must be served before Priority 4!")

        # Next should be Normal 1 (First in, first out among Priority 4)
        next_up3 = self.pq.dequeue()
        self.assertEqual(next_up3.patient_id, "N-01", "Normal cases must follow FIFO arrival order!")

        # Next should be Normal 2
        next_up4 = self.pq.dequeue()
        self.assertEqual(next_up4.patient_id, "N-02")

        # Queue should now be empty
        self.assertTrue(self.pq.is_empty)

    def test_fifo_order_within_same_priority(self):
        """Test that patients with same priority maintain strict FIFO order."""
        p_a = Patient("E-A", "Emerg A", 45, "M", "555-A", "O+", "Severe Trauma", priority=1)
        p_b = Patient("E-B", "Emerg B", 50, "F", "555-B", "A+", "Severe Asthma", priority=1)
        p_c = Patient("E-C", "Emerg C", 65, "M", "555-C", "B+", "Anaphylaxis", priority=1)

        self.pq.enqueue(p_a)
        self.pq.enqueue(p_b)
        self.pq.enqueue(p_c)

        self.assertEqual(self.pq.dequeue().patient_id, "E-A")
        self.assertEqual(self.pq.dequeue().patient_id, "E-B")
        self.assertEqual(self.pq.dequeue().patient_id, "E-C")

    def test_re_triage_escalation(self):
        """Test re-triaging a normal patient to emergency status."""
        p_norm = Patient("P-300", "Patient Deteriorating", 35, "F", "555-0", "O+", "Mild Pain", priority=4)
        p_norm2 = Patient("P-301", "Patient Waiting", 40, "M", "555-1", "A+", "Ear Infection", priority=4)

        self.pq.enqueue(p_norm)
        self.pq.enqueue(p_norm2)

        # Condition deteriorates: elevate to Priority 1
        success = self.pq.re_triage("P-300", new_priority=1)
        self.assertTrue(success)

        # Now P-300 must be next in line
        next_patient = self.pq.dequeue()
        self.assertEqual(next_patient.patient_id, "P-300")
        self.assertEqual(next_patient.priority, 1)


if __name__ == '__main__':
    unittest.main()
