/**
 * AuraCare Hospital Emergency Management System - Client Application
 * Priority Queue & Dynamic Linked List Management
 */

// Application State
let currentDashboardData = null;
let currentQueueData = [];
let allRecordsData = [];
let refreshTimer = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    fetchLiveState();
    // Auto refresh queue and stats every 8 seconds
    refreshTimer = setInterval(fetchLiveState, 8000);
});

/* ==========================================================================
   Tab Navigation
   ========================================================================== */
function switchTab(tabId) {
    // Update active tab buttons
    document.querySelectorAll('.nav-tab').forEach(tab => {
        if (tab.getAttribute('data-tab') === tabId) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Update tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        if (pane.id === tabId) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });

    // Lazy load specific tab content
    if (tabId === 'tab-records') {
        fetchRecords();
    } else if (tabId === 'tab-linked-list') {
        fetchLinkedListGraph();
    }
}

/* ==========================================================================
   Fetch & Render Real-time Dashboard & Queue
   ========================================================================== */
async function fetchLiveState() {
    try {
        const [dashRes, queueRes] = await Promise.all([
            fetch('/api/dashboard'),
            fetch('/api/queue')
        ]);

        const dashJson = await dashRes.json();
        const queueJson = await queueRes.json();

        if (dashJson.success && dashJson.data) {
            currentDashboardData = dashJson.data;
            updateDashboardKPIs(dashJson.data);
            renderBays(dashJson.data.bays);
        }

        if (queueRes.ok && queueJson.success) {
            currentQueueData = queueJson.queue;
            renderQueue(queueJson.queue);
        }
    } catch (err) {
        console.error('Error fetching live system state:', err);
    }
}

function updateDashboardKPIs(data) {
    document.getElementById('kpi-waiting-count').textContent = data.waiting_in_queue;
    document.getElementById('kpi-p1-count').textContent = data.critical_cases_waiting || 0;
    document.getElementById('kpi-treatment-count').textContent = data.under_treatment;
    document.getElementById('kpi-available-bays').textContent = data.available_bays;
    document.getElementById('kpi-p4-count').textContent = (data.queue_by_priority && data.queue_by_priority[4]) || 0;
    document.getElementById('kpi-linked-list-nodes').textContent = data.total_registered;

    // Badges in navigation
    document.getElementById('nav-queue-count').textContent = data.waiting_in_queue;
    document.getElementById('nav-bays-occupied').textContent = `${data.under_treatment}/${data.total_bays}`;
    document.getElementById('nav-records-count').textContent = data.total_registered;
}

/* ==========================================================================
   Live Queue Rendering
   ========================================================================== */
function renderQueue(queue) {
    const container = document.getElementById('queue-container');
    if (!queue || queue.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-clipboard-check"></i>
                <h3>Emergency Queue is Currently Empty</h3>
                <p>No patients waiting for triage triage or clinical beds at this moment.</p>
                <button class="btn btn-emerald" onclick="openRegistrationModal()">
                    <i class="fa-solid fa-user-plus"></i> Register Patient
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = queue.map((p, idx) => {
        const isNextUp = idx === 0;
        const pLevel = p.priority;
        const pBadgeClass = `badge-p${pLevel}`;
        const pDotClass = `dot-p${pLevel}`;
        
        // Vitals checks
        const spo2Warning = p.vitals.spo2 < 93 ? 'warning' : '';
        const hrWarning = (p.vitals.heart_rate > 110 || p.vitals.heart_rate < 50) ? 'warning' : '';

        return `
            <div class="queue-card p-${pLevel}">
                <div class="queue-card-header">
                    <div class="queue-rank-badge ${isNextUp ? 'next-up' : ''}">
                        <i class="fa-solid ${isNextUp ? 'fa-bell text-white' : 'fa-hashtag'}"></i>
                        ${isNextUp ? 'NEXT IN LINE' : `Queue #${p.queue_position}`}
                    </div>
                    <div class="priority-badge-tag ${pBadgeClass}">
                        <span class="legend-dot ${pDotClass}"></span>
                        ${p.priority_info.badge}
                    </div>
                </div>

                <div class="queue-card-body">
                    <div class="patient-info-row">
                        <span class="patient-name">${escapeHtml(p.name)}</span>
                        <span class="patient-id-tag">${p.patient_id}</span>
                        <div class="patient-meta-pills">
                            <span>${p.age} yrs</span> &bull;
                            <span>${p.gender}</span> &bull;
                            <strong>${p.blood_group}</strong>
                        </div>
                    </div>

                    <div class="complaint-box" style="margin-top: 10px;">
                        <i class="fa-solid fa-notes-medical" style="color: var(--primary);"></i>
                        <strong>Chief Complaint:</strong> ${escapeHtml(p.chief_complaint)}
                    </div>

                    <div class="vitals-ribbon" style="margin-top: 12px;">
                        <div class="vital-chip ${hrWarning}">
                            <span class="vital-label"><i class="fa-solid fa-heart-pulse text-rose"></i> Pulse</span>
                            <span class="vital-val">${p.vitals.heart_rate} <small>bpm</small></span>
                        </div>
                        <div class="vital-chip">
                            <span class="vital-label"><i class="fa-solid fa-gauge-high text-violet"></i> BP</span>
                            <span class="vital-val">${p.vitals.blood_pressure}</span>
                        </div>
                        <div class="vital-chip ${spo2Warning}">
                            <span class="vital-label"><i class="fa-solid fa-lungs text-cyan"></i> SpO2</span>
                            <span class="vital-val">${p.vitals.spo2}%</span>
                        </div>
                        <div class="vital-chip">
                            <span class="vital-label"><i class="fa-solid fa-temperature-half text-amber"></i> Temp</span>
                            <span class="vital-val">${p.vitals.temperature}°F</span>
                        </div>
                    </div>
                </div>

                <div class="queue-footer">
                    <div class="wait-timer">
                        <i class="fa-regular fa-clock"></i>
                        <span>Waiting: ${p.wait_time_minutes} min${p.wait_time_minutes === 1 ? '' : 's'}</span>
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-outline-cyan btn-sm" onclick="openRetriageModal('${p.patient_id}', '${escapeHtml(p.name)}', ${p.priority})" title="Adjust clinical priority">
                            <i class="fa-solid fa-arrows-up-down"></i> Re-Triage
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="admitSpecificPatient('${p.patient_id}')" title="Admit to available bed">
                            <i class="fa-solid fa-bed"></i> Admit
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

/* ==========================================================================
   Treatment Bays Rendering
   ========================================================================== */
function renderBays(bays) {
    const container = document.getElementById('bays-container');
    if (!bays || bays.length === 0) return;

    container.innerHTML = bays.map(bay => {
        const isOccupied = bay.patient_id !== null && bay.patient !== null;
        const patient = bay.patient;

        if (isOccupied && patient) {
            const pLevel = patient.priority;
            return `
                <div class="bay-card occupied">
                    <div class="bay-header">
                        <div class="bay-title-group">
                            <i class="fa-solid fa-bed-pulse bay-icon text-indigo"></i>
                            <div>
                                <div class="bay-name">${escapeHtml(bay.name)}</div>
                                <div class="bay-type">${bay.type}</div>
                            </div>
                        </div>
                        <span class="bay-status-badge status-occupied">
                            <i class="fa-solid fa-stethoscope"></i> Occupied
                        </span>
                    </div>

                    <div class="bay-body">
                        <div>
                            <div class="patient-info-row">
                                <span class="patient-name">${escapeHtml(patient.name)}</span>
                                <span class="patient-id-tag">${patient.patient_id}</span>
                                <span class="priority-badge-tag badge-p${pLevel}" style="font-size: 10px; padding: 2px 8px;">
                                    ${patient.priority_info.badge}
                                </span>
                            </div>

                            <div class="complaint-box" style="margin-top: 10px;">
                                <strong>Admitted For:</strong> ${escapeHtml(patient.chief_complaint)}
                            </div>

                            <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 6px;">
                                <div class="doctor-badge">
                                    <i class="fa-solid fa-user-doctor text-indigo"></i>
                                    <span>${escapeHtml(patient.treatment.doctor || 'Attending Physician')}</span>
                                </div>
                                <div style="font-size: 11px; color: var(--text-muted);">
                                    <i class="fa-regular fa-clock"></i> Treatment Started: ${formatTime(patient.treatment.started_at)}
                                </div>
                            </div>
                        </div>

                        <div style="display: flex; gap: 8px; margin-top: 14px;">
                            <button class="btn btn-outline-cyan btn-sm" style="flex: 1;" onclick="viewPatientChart('${patient.patient_id}')">
                                <i class="fa-solid fa-file-waveform"></i> View Record
                            </button>
                            <button class="btn btn-indigo btn-sm" style="flex: 1;" onclick="openTreatmentModal('${patient.patient_id}', '${escapeHtml(patient.name)}', '${escapeHtml(bay.name)}')">
                                <i class="fa-solid fa-circle-check"></i> Complete Treatment
                            </button>
                        </div>
                    </div>
                </div>
            `;
        } else {
            return `
                <div class="bay-card vacant">
                    <div class="bay-header">
                        <div class="bay-title-group">
                            <i class="fa-solid fa-bed bay-icon text-emerald"></i>
                            <div>
                                <div class="bay-name">${escapeHtml(bay.name)}</div>
                                <div class="bay-type">${bay.type}</div>
                            </div>
                        </div>
                        <span class="bay-status-badge status-vacant">
                            <i class="fa-solid fa-circle-dot"></i> Vacant
                        </span>
                    </div>

                    <div class="bay-body">
                        <div class="vacant-prompt">
                            <i class="fa-solid fa-heart-circle-plus"></i>
                            <div style="font-weight: 700; color: var(--text-main); font-size: 14px;">Bay Ready For Patient</div>
                            <div style="font-size: 12px; margin-top: 4px;">Cleaned, sanitized and equipped with vitals monitors</div>
                        </div>

                        <button class="btn btn-emerald btn-sm" onclick="callNextPatient('${bay.id}')">
                            <i class="fa-solid fa-user-plus"></i> Admit Highest Priority Patient
                        </button>
                    </div>
                </div>
            `;
        }
    }).join('');
}

/* ==========================================================================
   Patient Records (Linked List Store)
   ========================================================================== */
async function fetchRecords() {
    try {
        const searchVal = document.getElementById('record-search-input').value.trim();
        const pVal = document.getElementById('filter-priority').value;
        const sVal = document.getElementById('filter-status').value;

        const params = new URLSearchParams({
            search: searchVal,
            priority: pVal,
            status: sVal
        });

        const res = await fetch(`/api/patients?${params.toString()}`);
        const data = await res.json();

        if (data.success) {
            allRecordsData = data.records;
            renderRecordsTable(data.records);
            document.getElementById('records-count-text').textContent = `Showing ${data.records.length} of ${data.total_records} records in linked list`;
        }
    } catch (err) {
        console.error('Error fetching patient records:', err);
    }
}

function filterRecords() {
    fetchRecords();
}

function renderRecordsTable(records) {
    const tbody = document.getElementById('records-table-body');
    if (!records || records.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center" style="padding: 30px; color: var(--text-muted);">
                    <i class="fa-solid fa-folder-open" style="font-size: 24px; margin-bottom: 8px; display: block;"></i>
                    No patient records found in the linked list matching the current criteria.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = records.map(p => {
        let statusBadge = '';
        if (p.status === 'waiting') {
            statusBadge = `<span class="status-tag status-waiting"><i class="fa-solid fa-clock"></i> Waiting In Queue</span>`;
        } else if (p.status === 'under_treatment') {
            statusBadge = `<span class="status-tag status-under_treatment"><i class="fa-solid fa-bed-pulse"></i> In ${escapeHtml(p.treatment.bay_or_bed || 'Bay')}</span>`;
        } else if (p.status === 'completed') {
            statusBadge = `<span class="status-tag status-completed"><i class="fa-solid fa-circle-check"></i> Treated & Discharged</span>`;
        }

        return `
            <tr>
                <td><strong class="ds-code">${p.patient_id}</strong></td>
                <td>
                    <div style="font-weight: 700; color: var(--text-main);">${escapeHtml(p.name)}</div>
                    <div style="font-size: 11px; color: var(--text-muted);">${p.age} yrs &bull; ${p.gender} &bull; ${p.blood_group}</div>
                </td>
                <td>
                    <div style="max-width: 240px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(p.chief_complaint)}">
                        ${escapeHtml(p.chief_complaint)}
                    </div>
                </td>
                <td>
                    <span class="priority-badge-tag badge-p${p.priority}" style="font-size: 10px; padding: 3px 8px;">
                        ${p.priority_info.badge}
                    </span>
                </td>
                <td>
                    <span style="font-size: 11px; font-family: monospace;">
                        HR: ${p.vitals.heart_rate} | O2: ${p.vitals.spo2}%
                    </span>
                </td>
                <td>${statusBadge}</td>
                <td>
                    <span style="font-size: 11px; color: var(--text-muted);">${p.registration_time.split(' ')[1] || p.registration_time}</span>
                </td>
                <td class="text-right">
                    <div style="display: flex; gap: 4px; justify-content: flex-end;">
                        <button class="btn btn-outline-cyan btn-sm" onclick="viewPatientChart('${p.patient_id}')" title="View Full Chart">
                            <i class="fa-solid fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-rose btn-sm" onclick="deletePatientRecord('${p.patient_id}')" title="Delete from Linked List">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/* ==========================================================================
   Linked List Visualizer
   ========================================================================== */
async function fetchLinkedListGraph() {
    try {
        const res = await fetch('/api/linked-list/debug');
        const data = await res.json();

        if (data.success && data.data) {
            renderLinkedListGraph(data.data);
        }
    } catch (err) {
        console.error('Error fetching linked list structure:', err);
    }
}

function renderLinkedListGraph(graph) {
    document.getElementById('ds-head-id').textContent = graph.head_id || 'NULL (Empty)';
    document.getElementById('ds-tail-id').textContent = graph.tail_id || 'NULL (Empty)';
    document.getElementById('ds-node-count').textContent = graph.total_nodes;

    const container = document.getElementById('linked-list-graph-nodes');
    if (!graph.nodes || graph.nodes.length === 0) {
        container.innerHTML = `
            <div class="ds-terminal-node">HEAD &rarr; NULL (Linked list is currently empty)</div>
        `;
        return;
    }

    let html = `<div class="ds-terminal-node"><i class="fa-solid fa-flag"></i> HEAD</div>`;

    graph.nodes.forEach((node, idx) => {
        const pColor = `badge-p${node.priority}`;
        html += `
            <div class="ds-pointer-arrow">
                <i class="fa-solid fa-arrows-left-right"></i>
                <span class="ds-arrow-label">doubly-linked</span>
            </div>
            <div class="ds-node-block" onclick="viewPatientChart('${node.patient_id}')" style="cursor: pointer;" title="Click to view patient details">
                <div class="ds-node-header">
                    <span>Node #${node.index}</span>
                    <span style="font-weight: 700; color: #0284c7;">${node.node_id}</span>
                </div>
                <div class="ds-node-body">
                    <div class="ds-node-patient">${escapeHtml(node.name)}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px;">
                        <span class="ds-code">${node.patient_id}</span>
                        <span class="priority-badge-tag ${pColor}" style="font-size: 9px; padding: 1px 6px;">
                            P${node.priority}
                        </span>
                    </div>
                    <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">
                        Status: <strong>${node.status}</strong>
                    </div>
                </div>
                <div class="ds-pointer-strip">
                    <div>prev: ${node.prev_id ? `<span style="color:#0891b2;">${node.prev_id}</span>` : '<span style="color:#94a3b8;">NULL</span>'}</div>
                    <div style="text-align: right;">next: ${node.next_id ? `<span style="color:#0891b2;">${node.next_id}</span>` : '<span style="color:#94a3b8;">NULL</span>'}</div>
                </div>
            </div>
        `;
    });

    html += `
        <div class="ds-pointer-arrow">
            <i class="fa-solid fa-arrow-right"></i>
        </div>
        <div class="ds-terminal-node"><i class="fa-solid fa-anchor"></i> TAIL &rarr; NULL</div>
    `;

    container.innerHTML = html;
}

/* ==========================================================================
   Patient Registration & Smart Triage
   ========================================================================== */
function openRegistrationModal() {
    document.getElementById('patient-registration-form').reset();
    document.getElementById('rad-p4').checked = true;
    smartTriageSuggest();
    openModal('modal-registration');
}

function smartTriageSuggest() {
    const complaint = (document.getElementById('reg-complaint').value || '').toLowerCase();
    const hr = parseInt(document.getElementById('reg-hr').value || 80, 10);
    const spo2 = parseInt(document.getElementById('reg-spo2').value || 98, 10);

    let suggestedPriority = 4;
    let reason = "Normal vitals and mild symptoms. Placed in standard FIFO queue.";

    // Critical Emergency Keywords & Vitals (P1)
    const p1Keywords = ['cardiac', 'arrest', 'crushing chest pain', 'heart attack', 'unconscious', 'respiratory failure', 'not breathing', 'severe bleeding', 'code red', 'anaphylaxis shock'];
    const p2Keywords = ['severe asthma', 'wheezing', 'open fracture', 'severe pain', 'stroke', 'heavy bleeding', 'head trauma', 'stridor'];
    const p3Keywords = ['cut', 'laceration', 'broken', 'fracture', 'sprain', 'stitches', 'vomiting', 'moderate pain', 'dehydration'];

    if (p1Keywords.some(kw => complaint.includes(kw)) || spo2 < 90 || hr > 145) {
        suggestedPriority = 1;
        reason = "Immediate Life Threat detected! Low SpO2 or critical symptoms indicate Emergency Resuscitation (P1). Skips to front of queue!";
    } else if (p2Keywords.some(kw => complaint.includes(kw)) || spo2 < 93 || hr > 120) {
        suggestedPriority = 2;
        reason = "Very Urgent clinical presentation detected. Recommended: Priority 2 (Emergency). Target time < 15 mins.";
    } else if (p3Keywords.some(kw => complaint.includes(kw))) {
        suggestedPriority = 3;
        reason = "Moderate acute presentation detected. Recommended: Priority 3 (Urgent). Target time < 60 mins.";
    }

    const expElem = document.getElementById('suggestion-explanation');
    if (expElem) {
        expElem.textContent = reason;
    }

    // Auto-select radio button if user hasn't manually overridden
    const targetRad = document.getElementById(`rad-p${suggestedPriority}`);
    if (targetRad) {
        targetRad.checked = true;
    }
}

async function handleRegistrationSubmit(event) {
    event.preventDefault();

    const selectedPriority = document.querySelector('input[name="priority_selection"]:checked')?.value || 4;

    const payload = {
        name: document.getElementById('reg-name').value.trim(),
        age: parseInt(document.getElementById('reg-age').value, 10),
        gender: document.getElementById('reg-gender').value,
        contact: document.getElementById('reg-contact').value.trim(),
        blood_group: document.getElementById('reg-blood').value,
        chief_complaint: document.getElementById('reg-complaint').value.trim(),
        priority: parseInt(selectedPriority, 10),
        heart_rate: parseInt(document.getElementById('reg-hr').value, 10),
        blood_pressure: document.getElementById('reg-bp').value.trim(),
        spo2: parseInt(document.getElementById('reg-spo2').value, 10),
        temperature: parseFloat(document.getElementById('reg-temp').value),
        notes: document.getElementById('reg-notes').value.trim()
    };

    try {
        const res = await fetch('/api/patients/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.success) {
            closeModal('modal-registration');
            showToast(data.message, 'success');
            fetchLiveState();
            fetchRecords();
            fetchLinkedListGraph();
        } else {
            showToast(data.message || 'Registration failed', 'error');
        }
    } catch (err) {
        showToast('Error registering patient: ' + err.message, 'error');
    }
}

/* ==========================================================================
   Priority Queue Actions
   ========================================================================== */
async function callNextPatient(bayId = null) {
    try {
        const res = await fetch('/api/queue/call-next', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bay_id: bayId })
        });

        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            fetchLiveState();
            fetchRecords();
            fetchLinkedListGraph();
        } else {
            showToast(data.message, 'info');
        }
    } catch (err) {
        showToast('Error calling patient: ' + err.message, 'error');
    }
}

async function admitSpecificPatient(patientId, bayId = null) {
    try {
        const res = await fetch('/api/queue/admit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_id: patientId, bay_id: bayId })
        });

        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            fetchLiveState();
            fetchRecords();
            fetchLinkedListGraph();
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        showToast('Error admitting patient: ' + err.message, 'error');
    }
}

/* ==========================================================================
   Re-Triage Action
   ========================================================================== */
function openRetriageModal(patientId, patientName, currentPriority) {
    document.getElementById('retriage-patient-id').value = patientId;
    document.getElementById('retriage-patient-name').textContent = `Patient: ${patientName} (${patientId}) — Currently Priority ${currentPriority}`;
    document.getElementById('retriage-new-priority').value = currentPriority;
    document.getElementById('retriage-reason').value = '';
    openModal('modal-retriage');
}

async function handleRetriageSubmit(event) {
    event.preventDefault();
    const patientId = document.getElementById('retriage-patient-id').value;
    const priority = parseInt(document.getElementById('retriage-new-priority').value, 10);
    const reason = document.getElementById('retriage-reason').value.trim();

    try {
        const res = await fetch('/api/patients/re-triage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_id: patientId, priority: priority, reason: reason })
        });

        const data = await res.json();
        if (data.success) {
            closeModal('modal-retriage');
            showToast(data.message, 'success');
            fetchLiveState();
            fetchRecords();
            fetchLinkedListGraph();
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        showToast('Error re-triaging: ' + err.message, 'error');
    }
}

/* ==========================================================================
   Treatment Completion & Discharge
   ========================================================================== */
function openTreatmentModal(patientId, patientName, bayName) {
    document.getElementById('treat-patient-id').value = patientId;
    document.getElementById('treat-patient-summary').innerHTML = `
        <div style="font-weight: 700; color: var(--text-main); font-size: 14px;">${patientName} (${patientId})</div>
        <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">Assigned Bed: <strong>${bayName}</strong></div>
    `;
    document.getElementById('treat-diagnosis').value = '';
    document.getElementById('treat-medications').value = '';
    document.getElementById('treat-notes').value = '';
    openModal('modal-treatment');
}

async function handleTreatmentCompletion(event) {
    event.preventDefault();
    const patientId = document.getElementById('treat-patient-id').value;
    const payload = {
        patient_id: patientId,
        diagnosis: document.getElementById('treat-diagnosis').value.trim(),
        medications: document.getElementById('treat-medications').value.trim(),
        outcome: document.getElementById('treat-outcome').value,
        notes: document.getElementById('treat-notes').value.trim()
    };

    try {
        const res = await fetch('/api/treatment/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.success) {
            closeModal('modal-treatment');
            showToast(data.message, 'success');
            fetchLiveState();
            fetchRecords();
            fetchLinkedListGraph();
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        showToast('Error completing treatment: ' + err.message, 'error');
    }
}

/* ==========================================================================
   View Medical Chart / Slip
   ========================================================================== */
async function viewPatientChart(patientId) {
    try {
        const res = await fetch(`/api/patients/${patientId}`);
        const data = await res.json();

        if (data.success && data.patient) {
            const p = data.patient;
            const container = document.getElementById('patient-chart-content');

            container.innerHTML = `
                <div class="chart-slip">
                    <div class="chart-header">
                        <div>
                            <div class="chart-hospital-name">AuraCare Emergency Department</div>
                            <div style="font-size: 11px; color: var(--text-muted);">Dynamic Linked List Record Store &bull; Emergency Triage</div>
                        </div>
                        <div style="text-align: right;">
                            <span class="priority-badge-tag badge-p${p.priority}">${p.priority_info.badge}</span>
                            <div class="ds-code" style="margin-top: 4px;">${p.patient_id}</div>
                        </div>
                    </div>

                    <div class="chart-section">
                        <div class="chart-section-title">Patient Demographics</div>
                        <div class="chart-grid-2">
                            <div><strong>Name:</strong> ${escapeHtml(p.name)}</div>
                            <div><strong>Age / Gender:</strong> ${p.age} yrs / ${p.gender}</div>
                            <div><strong>Blood Group:</strong> ${p.blood_group}</div>
                            <div><strong>Contact:</strong> ${escapeHtml(p.contact || 'None')}</div>
                        </div>
                    </div>

                    <div class="chart-section">
                        <div class="chart-section-title">Emergency Presentation & Vitals</div>
                        <div style="margin-bottom: 8px;"><strong>Chief Complaint:</strong> ${escapeHtml(p.chief_complaint)}</div>
                        <div class="chart-grid-2">
                            <div><strong>Heart Rate:</strong> ${p.vitals.heart_rate} bpm</div>
                            <div><strong>Blood Pressure:</strong> ${p.vitals.blood_pressure}</div>
                            <div><strong>SpO2:</strong> ${p.vitals.spo2}%</div>
                            <div><strong>Temperature:</strong> ${p.vitals.temperature}°F</div>
                        </div>
                    </div>

                    <div class="chart-section">
                        <div class="chart-section-title">Clinical Triage & Timestamps</div>
                        <div class="chart-grid-2">
                            <div><strong>Triage Category:</strong> ${p.priority_info.name}</div>
                            <div><strong>Registered At:</strong> ${p.registration_time}</div>
                            <div><strong>Current Status:</strong> <span style="text-transform: capitalize; font-weight: 700;">${p.status.replace('_', ' ')}</span></div>
                            <div><strong>Elapsed Wait Time:</strong> ${p.wait_time_minutes} minutes</div>
                        </div>
                    </div>

                    ${p.treatment && p.treatment.started_at ? `
                        <div class="chart-section">
                            <div class="chart-section-title">Treatment & Medical Discharge Summary</div>
                            <div class="chart-grid-2" style="margin-bottom: 6px;">
                                <div><strong>Attending Doctor:</strong> ${escapeHtml(p.treatment.doctor || 'N/A')}</div>
                                <div><strong>Treatment Bay:</strong> ${escapeHtml(p.treatment.bay_or_bed || 'N/A')}</div>
                                <div><strong>Treatment Began:</strong> ${formatTime(p.treatment.started_at)}</div>
                                <div><strong>Completed / Discharged:</strong> ${p.treatment.completed_at ? formatTime(p.treatment.completed_at) : 'In Progress'}</div>
                            </div>
                            <div style="margin-top: 6px;"><strong>Clinical Diagnosis:</strong> ${escapeHtml(p.treatment.diagnosis || 'Pending completion')}</div>
                            <div style="margin-top: 4px;"><strong>Medications Administered:</strong> ${escapeHtml(p.treatment.medications || 'None recorded')}</div>
                            <div style="margin-top: 4px;"><strong>Outcome / Disposition:</strong> ${escapeHtml(p.treatment.outcome || 'Under observation')}</div>
                        </div>
                    ` : ''}

                    ${p.notes ? `
                        <div class="chart-section">
                            <div class="chart-section-title">Clinical Notes & Allergies</div>
                            <p style="font-size: 12px; color: #475569;">${escapeHtml(p.notes)}</p>
                        </div>
                    ` : ''}
                </div>
            `;

            openModal('modal-patient-chart');
        }
    } catch (err) {
        showToast('Error loading chart: ' + err.message, 'error');
    }
}

function printPatientChart() {
    window.print();
}

async function deletePatientRecord(patientId) {
    if (!confirm(`Are you sure you want to permanently remove patient ${patientId} from the linked list and queue?`)) {
        return;
    }

    try {
        const res = await fetch(`/api/patients/${patientId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            fetchLiveState();
            fetchRecords();
            fetchLinkedListGraph();
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        showToast('Error deleting record: ' + err.message, 'error');
    }
}

/* ==========================================================================
   Demo Seed & Reset
   ========================================================================== */
async function seedDemoData() {
    try {
        const res = await fetch('/api/demo/seed', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            fetchLiveState();
            fetchRecords();
            fetchLinkedListGraph();
        }
    } catch (err) {
        showToast('Error seeding demo data', 'error');
    }
}

async function resetAllData() {
    if (!confirm("Are you sure you want to clear all patient records and reset the queue?")) return;
    try {
        const res = await fetch('/api/demo/reset', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'info');
            fetchLiveState();
            fetchRecords();
            fetchLinkedListGraph();
        }
    } catch (err) {
        showToast('Error resetting data', 'error');
    }
}

/* ==========================================================================
   Modal Helpers
   ========================================================================== */
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('open');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('open');
}

/* ==========================================================================
   Toast Notification System
   ========================================================================== */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-circle-check';
    if (type === 'error') icon = 'fa-circle-exclamation';

    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/* ==========================================================================
   Utility Functions
   ========================================================================== */
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

function formatTime(isoStr) {
    if (!isoStr) return '';
    try {
        const dt = new Date(isoStr);
        return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
        return isoStr;
    }
}
