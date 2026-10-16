"""
Core Data Structures for Hospital Emergency Management System
1. Patient: Model representing patient information and clinical status
2. PatientNode: Node for dynamic Doubly Linked List storage
3. PatientLinkedList: Dynamic linked list for patient record maintenance
4. EmergencyPriorityQueue: Priority queue where emergency cases are handled first,
   while normal cases follow strict FIFO (First-In, First-Out) order.
"""

from datetime import datetime
import time
from typing import Optional, List, Dict, Any


class Patient:
    """Represents a patient record in the hospital system."""
    
    # Priority Levels
    PRIORITY_LEVELS = {
        1: {"name": "Immediate / Resuscitation", "color": "#ef4444", "badge": "P1 - CRITICAL", "target_mins": "0 min"},
        2: {"name": "Very Urgent / Emergency", "color": "#f97316", "badge": "P2 - EMERGENCY", "target_mins": "< 15 mins"},
        3: {"name": "Urgent / Semi-Urgent", "color": "#eab308", "badge": "P3 - URGENT", "target_mins": "< 60 mins"},
        4: {"name": "Standard / Normal (FIFO)", "color": "#10b981", "badge": "P4 - NORMAL", "target_mins": "< 120 mins"}
    }

    def __init__(
        self,
        patient_id: str,
        name: str,
        age: int,
        gender: str,
        contact: str,
        blood_group: str,
        chief_complaint: str,
        priority: int = 4,
        vitals: Optional[Dict[str, Any]] = None,
        notes: str = ""
    ):
        self.patient_id = patient_id
        self.name = name
        self.age = int(age)
        self.gender = gender
        self.contact = contact
        self.blood_group = blood_group
        self.chief_complaint = chief_complaint
        
        # Priority level: 1 (Highest/Critical) to 4 (Normal/FIFO)
        self.priority = int(priority) if int(priority) in self.PRIORITY_LEVELS else 4
        
        # Vitals default
        self.vitals = vitals or {
            "heart_rate": 80,
            "blood_pressure": "120/80",
            "spo2": 98,
            "temperature": 98.6
        }
        
        self.notes = notes
        self.registration_time = datetime.now()
        self.arrival_timestamp = time.time()
        
        # Status: 'waiting', 'under_treatment', 'completed'
        self.status = "waiting"
        
        # Treatment details when attended
        self.treatment = {
            "doctor": None,
            "bay_or_bed": None,
            "started_at": None,
            "completed_at": None,
            "diagnosis": "",
            "medications": "",
            "outcome": None  # 'Discharged', 'Admitted to Ward', 'Transferred to ICU'
        }

    @property
    def priority_info(self) -> Dict[str, str]:
        return self.PRIORITY_LEVELS.get(self.priority, self.PRIORITY_LEVELS[4])

    @property
    def wait_time_minutes(self) -> int:
        """Calculate minutes elapsed since arrival if still waiting or until treatment started."""
        if self.treatment["started_at"]:
            start_dt = datetime.fromisoformat(self.treatment["started_at"])
            return max(0, int((start_dt - self.registration_time).total_seconds() / 60))
        return max(0, int((datetime.now() - self.registration_time).total_seconds() / 60))

    def to_dict(self) -> Dict[str, Any]:
        """Convert patient object to JSON-serializable dictionary."""
        return {
            "patient_id": self.patient_id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "contact": self.contact,
            "blood_group": self.blood_group,
            "chief_complaint": self.chief_complaint,
            "priority": self.priority,
            "priority_info": self.priority_info,
            "vitals": self.vitals,
            "notes": self.notes,
            "registration_time": self.registration_time.strftime("%Y-%m-%d %H:%M:%S"),
            "arrival_timestamp": self.arrival_timestamp,
            "wait_time_minutes": self.wait_time_minutes,
            "status": self.status,
            "treatment": self.treatment
        }


class PatientNode:
    """
    Node in the Doubly Linked List storing a Patient record dynamically.
    Doubly linked structure allows forward and backward traversal and O(1) removal.
    """
    def __init__(self, patient: Patient):
        self.patient = patient
        self.prev: Optional['PatientNode'] = None
        self.next: Optional['PatientNode'] = None
        self.node_id = f"node_{hex(id(self))[-6:]}"

    def to_debug_dict(self) -> Dict[str, Any]:
        """Returns node information including pointer links for visual inspector."""
        return {
            "node_id": self.node_id,
            "patient_id": self.patient.patient_id,
            "name": self.patient.name,
            "priority": self.patient.priority,
            "status": self.patient.status,
            "prev_id": self.prev.node_id if self.prev else None,
            "prev_patient_id": self.prev.patient.patient_id if self.prev else None,
            "next_id": self.next.node_id if self.next else None,
            "next_patient_id": self.next.patient.patient_id if self.next else None,
        }


class PatientLinkedList:
    """
    Dynamic Doubly Linked List for patient records maintenance.
    Stores all patient records created dynamically in memory.
    """
    def __init__(self):
        self.head: Optional[PatientNode] = None
        self.tail: Optional[PatientNode] = None
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    @property
    def is_empty(self) -> bool:
        return self.head is None

    def append(self, patient: Patient) -> PatientNode:
        """Dynamically append a new patient node to the end of the linked list."""
        new_node = PatientNode(patient)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.prev = self.tail
            if self.tail:
                self.tail.next = new_node
            self.tail = new_node
        self._size += 1
        return new_node

    def find_node(self, patient_id: str) -> Optional[PatientNode]:
        """Search for a node by patient_id using linked list traversal."""
        current = self.head
        while current is not None:
            if current.patient.patient_id == patient_id:
                return current
            current = current.next
        return None

    def find(self, patient_id: str) -> Optional[Patient]:
        """Search and return the Patient object with given patient_id."""
        node = self.find_node(patient_id)
        return node.patient if node else None

    def update(self, patient_id: str, **kwargs) -> bool:
        """Update fields of an existing patient in the linked list."""
        patient = self.find(patient_id)
        if not patient:
            return False
        for key, value in kwargs.items():
            if hasattr(patient, key):
                setattr(patient, key, value)
        return True

    def delete(self, patient_id: str) -> bool:
        """Remove a patient node from the linked list by patient_id."""
        node = self.find_node(patient_id)
        if not node:
            return False

        # If node is head
        if node == self.head:
            self.head = node.next
            if self.head:
                self.head.prev = None
            else:
                self.tail = None
        # If node is tail
        elif node == self.tail:
            self.tail = node.prev
            if self.tail:
                self.tail.next = None
            else:
                self.head = None
        # Node in the middle
        else:
            if node.prev:
                node.prev.next = node.next
            if node.next:
                node.next.prev = node.prev

        self._size -= 1
        return True

    def to_list(self) -> List[Dict[str, Any]]:
        """Traverse the linked list from head to tail and return list of dictionaries."""
        records = []
        current = self.head
        while current is not None:
            records.append(current.patient.to_dict())
            current = current.next
        return records

    def to_visual_graph(self) -> Dict[str, Any]:
        """Return visual representation of the linked list data structure for frontend display."""
        nodes = []
        current = self.head
        index = 0
        while current is not None:
            node_info = current.to_debug_dict()
            node_info["index"] = index
            nodes.append(node_info)
            current = current.next
            index += 1

        return {
            "head_id": self.head.node_id if self.head else None,
            "tail_id": self.tail.node_id if self.tail else None,
            "total_nodes": self._size,
            "nodes": nodes
        }

    def clear(self):
        """Clear all records from the linked list."""
        self.head = None
        self.tail = None
        self._size = 0


class EmergencyPriorityQueue:
    """
    Priority Queue for Hospital Emergency Management.
    - Highest priority (Emergency / Critical, level 1) is served first.
    - Urgent cases (level 2 & 3) follow in priority order.
    - Standard / Normal cases (level 4) follow strict FIFO order.
    - Within the SAME priority tier, arrival order (FIFO) is strictly preserved!
    Implemented cleanly using priority buckets to guarantee O(1) tier lookup
    and stable FIFO order within each tier.
    """
    def __init__(self):
        # 4 Priority buckets (1 to 4)
        # Bucket 1: Immediate/Resuscitation
        # Bucket 2: High Emergency
        # Bucket 3: Urgent
        # Bucket 4: Normal (FIFO)
        self.buckets: Dict[int, List[Patient]] = {
            1: [],
            2: [],
            3: [],
            4: []
        }

    def __len__(self) -> int:
        return sum(len(q) for q in self.buckets.values())

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    def enqueue(self, patient: Patient):
        """Enqueue patient into their respective priority bucket preserving FIFO order."""
        p_level = patient.priority if patient.priority in self.buckets else 4
        patient.status = "waiting"
        self.buckets[p_level].append(patient)

    def dequeue(self) -> Optional[Patient]:
        """
        Dequeues the next patient to be treated:
        Checks highest priority tier (1, then 2, then 3, then 4).
        Takes the first patient from that tier (FIFO within priority).
        """
        for level in (1, 2, 3, 4):
            if self.buckets[level]:
                return self.buckets[level].pop(0)
        return None

    def peek(self) -> Optional[Patient]:
        """View the next patient in line without removing them."""
        for level in (1, 2, 3, 4):
            if self.buckets[level]:
                return self.buckets[level][0]
        return None

    def remove(self, patient_id: str) -> Optional[Patient]:
        """Remove a specific patient from the queue (e.g. if cancelled or transferred directly)."""
        for level in (1, 2, 3, 4):
            for i, p in enumerate(self.buckets[level]):
                if p.patient_id == patient_id:
                    return self.buckets[level].pop(i)
        return None

    def re_triage(self, patient_id: str, new_priority: int) -> bool:
        """
        Change priority for a patient currently in the queue (e.g. condition deteriorated).
        Moves the patient to the new priority bucket, placed at the front/time-ordered position.
        """
        if new_priority not in self.buckets:
            return False
        
        patient = self.remove(patient_id)
        if not patient:
            return False
            
        patient.priority = new_priority
        # Insert maintaining arrival timestamp order inside the new priority bucket
        bucket = self.buckets[new_priority]
        inserted = False
        for i, existing in enumerate(bucket):
            if patient.arrival_timestamp < existing.arrival_timestamp:
                bucket.insert(i, patient)
                inserted = True
                break
        if not inserted:
            bucket.append(patient)
        return True

    def get_ordered_list(self) -> List[Dict[str, Any]]:
        """
        Returns full queue in the exact sequence patients will be attended:
        Emergency tier 1 first (FIFO), then tier 2 (FIFO), then tier 3 (FIFO), then tier 4 (FIFO).
        """
        ordered = []
        position = 1
        for level in (1, 2, 3, 4):
            for patient in self.buckets[level]:
                item = patient.to_dict()
                item["queue_position"] = position
                ordered.append(item)
                position += 1
        return ordered

    def count_by_priority(self) -> Dict[int, int]:
        """Return patient counts waiting in each priority bucket."""
        return {lvl: len(self.buckets[lvl]) for lvl in (1, 2, 3, 4)}

    def clear(self):
        """Clear the priority queue."""
        for level in (1, 2, 3, 4):
            self.buckets[level].clear()
