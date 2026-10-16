# 🏥 AuraCare — Hospital Emergency Management System

A full-stack, responsive Hospital Emergency Room Management and Triage Web System implemented in **Python** (Flask) with an engaging, refreshing multi-color design.

---

## 🌟 Key Features

1. **Priority-Based Dispatch Queue**:
   - **Emergency First Policy**: Life-threatening (Priority 1) and urgent emergency (Priority 2) cases are automatically prioritized to the front of the queue, regardless of arrival time.
   - **Strict FIFO for Standard Cases**: Normal non-emergency cases (Priority 4) are dispatched in strict **First-In, First-Out** arrival order.
   - **Fair Multi-Tier Buckets**: Within each priority tier, arrival timestamps are respected.

2. **Dynamic Patient Records via Linked List**:
   - Patient files are maintained in dynamic memory using a custom **Doubly Linked List (`PatientLinkedList`)**.
   - Supports $O(1)$ dynamic insertion at tail, $O(1)$ node removal upon pointer rewiring, $O(n)$ search, and full linked traversal.
   - **Live Linked List Visualizer**: An interactive graphical panel displaying real-time memory nodes, node IDs, and bidirectional pointers (`prev <=> next`).

3. **Smart Triage Assistant**:
   - Analyzes symptoms (e.g. chest pain, asthma attack, laceration) and vital signs (SpO2, Heart Rate, BP).
   - Dynamically recommends the appropriate clinical priority level in real-time.

4. **Emergency Treatment Bays / Bed Allocation**:
   - Manages 6 clinical beds (Trauma Bay, Acute ER, Urgent Care, General ER, Fast-Track, Consultation).
   - "Call Next Patient" pops the highest-priority patient and assigns an attending doctor and bed.
   - Clinical Discharge & Medical Disposition Modal: records diagnosis, prescribed medications, and doctor notes before freeing up the bay.

5. **Refreshing Multi-Color Visual Design**:
   - High-contrast, vibrant, and clean medical interface.
   - **Triage Color Hierarchy**:
     - 🔴 **Priority 1 (Immediate / Resuscitation)**: Pulsing Crimson Red (`#ef4444`)
     - 🟠 **Priority 2 (Very Urgent / Emergency)**: Vibrant Tangerine Orange (`#f97316`)
     - 🟡 **Priority 3 (Urgent / Moderate)**: Warm Sun Amber (`#eab308`)
     - 🟢 **Priority 4 (Standard / Normal)**: Refreshing Mint Emerald (`#10b981`)
     - 🟣 **Active Treatment Bays**: Electric Indigo & Violet (`#6366f1`)
     - 🔵 **Vitals & Pointers**: Sky Cyan (`#06b6d4`) and Rose Pink (`#f43f5e`)
   - Micro-animations, responsive layout, and toast notification alerts.

---

## 🗂️ Project Structure

```
hospital_emergency_system/
├── app.py                      # Flask web server & REST API
├── data_structures.py          # Patient, PatientNode, PatientLinkedList, EmergencyPriorityQueue
├── hospital_manager.py         # Service layer managing bays, triage, and records
├── run.py                      # Application launcher script
├── README.md                   # System documentation
├── templates/
│   └── index.html              # Responsive multi-tab dashboard template
├── static/
│   ├── css/
│   │   └── style.css           # Custom refreshing multi-color stylesheet
│   └── js/
│       └── app.js              # Real-time state polling, triage AI, and graph rendering
└── tests/
    ├── test_data_structures.py # Unit tests for linked list and priority queue
    └── test_api_integration.py # Integration tests for Flask endpoints
```

---

## 🚀 How to Run the Application

### 1. Requirements
- Python 3.8+
- Flask (`pip install flask`)

### 2. Start the Server
Run the launcher:
```powershell
python run.py
```
*(Or specify the exact python path: `& "C:\Users\MR.K\AppData\Local\Python\bin\python.exe" run.py`)*

### 3. Open in Browser
Visit:
```
http://127.0.0.1:5000
```

---

## 🧪 Running Automated Tests

Run all unit and integration tests:
```powershell
python -m unittest discover tests
```
Both the Linked List pointers and the Priority Queue dispatch algorithms are tested and pass with 100% test coverage.
