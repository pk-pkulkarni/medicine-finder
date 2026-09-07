const state = {
  patients: [],
  documents: [],
  rows: [],
  activePatientId: null,
  search: ""
};

const el = {
  patientForm: document.querySelector("#patientForm"),
  patientName: document.querySelector("#patientName"),
  patientList: document.querySelector("#patientList"),
  activePatientTitle: document.querySelector("#activePatientTitle"),
  storageStatus: document.querySelector("#storageStatus"),
  searchInput: document.querySelector("#searchInput"),
  docCount: document.querySelector("#docCount"),
  medicineCount: document.querySelector("#medicineCount"),
  matchCount: document.querySelector("#matchCount"),
  documentForm: document.querySelector("#documentForm"),
  documentFile: document.querySelector("#documentFile"),
  visitDate: document.querySelector("#visitDate"),
  doctorName: document.querySelector("#doctorName"),
  symptoms: document.querySelector("#symptoms"),
  documentText: document.querySelector("#documentText"),
  resultScope: document.querySelector("#resultScope"),
  resultsTable: document.querySelector("#resultsTable"),
  documentList: document.querySelector("#documentList"),
  previewDialog: document.querySelector("#previewDialog"),
  previewTitle: document.querySelector("#previewTitle"),
  previewMeta: document.querySelector("#previewMeta"),
  previewFrame: document.querySelector("#previewFrame"),
  closePreview: document.querySelector("#closePreview")
};

function activePatient() {
  return state.patients.find((patient) => String(patient.id) === String(state.activePatientId)) || null;
}

function apiUrl(path, params = {}) {
  const url = new URL(path, window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
  });
  return url;
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

async function loadPatients() {
  const data = await requestJson("/api/patients/");
  state.patients = data.patients;
  if (!state.activePatientId && state.patients[0]) {
    state.activePatientId = state.patients[0].id;
  }
}

async function loadDocuments() {
  const data = await requestJson(apiUrl("/api/documents/", { patient_id: state.activePatientId }));
  state.documents = data.documents;
}

async function loadSearchRows() {
  const data = await requestJson(apiUrl("/api/search/", {
    patient_id: state.activePatientId,
    q: state.search
  }));
  state.rows = data.rows;
}

async function refresh() {
  await loadPatients();
  await loadDocuments();
  await loadSearchRows();
  render();
}

function formatDate(value) {
  if (!value) return "No date";
  return new Intl.DateTimeFormat(undefined, { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`));
}

function renderPatients() {
  if (!state.patients.length) {
    el.patientList.innerHTML = `<div class="empty-state">Add the first patient to start saving prescriptions.</div>`;
    return;
  }

  el.patientList.innerHTML = state.patients.map((patient) => {
    const active = String(patient.id) === String(state.activePatientId) ? " active" : "";
    return `
      <button class="patient-card${active}" data-patient-id="${patient.id}" type="button">
        <strong>${escapeHtml(patient.name)}</strong>
        <span>${patient.document_count} document${patient.document_count === 1 ? "" : "s"}</span>
      </button>
    `;
  }).join("");
}

function renderStats() {
  const selected = activePatient();
  const medicineCount = state.documents.reduce((total, document) => total + document.medicines.length, 0);

  el.activePatientTitle.textContent = selected ? selected.name : "All patients";
  el.storageStatus.textContent = "Django backend";
  el.docCount.textContent = state.documents.length;
  el.medicineCount.textContent = medicineCount;
  el.documentForm.hidden = !selected;
}

function renderResults() {
  el.matchCount.textContent = state.rows.length;
  el.resultScope.textContent = state.search ? `Matching "${state.search}"` : "All saved documents";

  if (!state.rows.length) {
    el.resultsTable.innerHTML = `<tr><td colspan="8">No matching prescription rows.</td></tr>`;
    return;
  }

  el.resultsTable.innerHTML = state.rows.map(({ document, medicine }) => `
    <tr>
      <td>${formatDate(document.visit_date)}</td>
      <td>${escapeHtml(document.patient_name)}</td>
      <td>${escapeHtml(document.symptoms || "Not noted")}</td>
      <td>
        <strong>${escapeHtml(medicine?.name || "No medicine detected")}</strong>
        <span class="subtext">${escapeHtml(medicine?.raw_line || document.doctor_name || "")}</span>
      </td>
      <td>${escapeHtml(medicine?.dosage || "Not detected")}</td>
      <td>${escapeHtml(medicine?.quantity || "Not detected")}</td>
      <td>${escapeHtml(medicine?.duration || medicine?.frequency || "Not detected")}</td>
      <td><button class="link-button" data-preview-id="${document.id}" type="button">${escapeHtml(document.file_name)}</button></td>
    </tr>
  `).join("");
}

function renderDocuments() {
  if (!state.documents.length) {
    el.documentList.innerHTML = `<div class="empty-state">No prescription documents saved for this view.</div>`;
    return;
  }

  el.documentList.innerHTML = state.documents.map((document) => `
    <article class="document-item">
      <h4>${escapeHtml(document.file_name)}</h4>
      <div>${formatDate(document.visit_date)}</div>
      <div>${escapeHtml(document.symptoms || "Symptoms not noted")}</div>
      <div>${escapeHtml(document.extraction_status || "Text extraction complete")}</div>
      <div class="document-actions">
        <button class="link-button" data-preview-id="${document.id}" type="button">Preview</button>
        <button class="delete-button" data-delete-id="${document.id}" type="button">Delete</button>
      </div>
    </article>
  `).join("");
}

function render() {
  renderPatients();
  renderStats();
  renderResults();
  renderDocuments();
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function addPatient(name) {
  const patient = await requestJson("/api/patients/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  state.activePatientId = patient.id;
  await refresh();
}

async function addDocument(form) {
  const patient = activePatient();
  const file = el.documentFile.files[0];
  if (!patient || !file) return;

  const payload = new FormData();
  payload.set("patient_id", patient.id);
  payload.set("file", file);
  payload.set("visit_date", form.get("visitDate"));
  payload.set("doctor_name", form.get("doctorName") || "");
  payload.set("symptoms", form.get("symptoms") || "");
  payload.set("document_text", form.get("documentText") || "");

  await requestJson("/api/documents/", {
    method: "POST",
    body: payload
  });

  el.documentForm.reset();
  el.visitDate.valueAsDate = new Date();
  await refresh();
}

async function deleteDocument(id) {
  await requestJson(`/api/documents/${id}/`, { method: "DELETE" });
  await refresh();
}

function previewDocument(id) {
  const document = state.documents.find((item) => String(item.id) === String(id))
    || state.rows.find((row) => String(row.document.id) === String(id))?.document;
  if (!document) return;

  el.previewTitle.textContent = document.file_name;
  el.previewMeta.textContent = `${formatDate(document.visit_date)} · ${document.doctor_name || "Doctor not noted"}`;
  el.previewFrame.innerHTML = document.file_type.startsWith("image/")
    ? `<img alt="${escapeHtml(document.file_name)}" src="${document.file_url}" />`
    : `<iframe title="${escapeHtml(document.file_name)}" src="${document.file_url}"></iframe>`;
  el.previewDialog.showModal();
}

function wireEvents() {
  el.patientForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = el.patientName.value.trim();
    if (!name) return;
    await addPatient(name);
    el.patientForm.reset();
  });

  el.patientList.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-patient-id]");
    if (!button) return;
    state.activePatientId = button.dataset.patientId;
    await refresh();
  });

  el.searchInput.addEventListener("input", async (event) => {
    state.search = event.target.value.trim();
    await loadSearchRows();
    renderResults();
  });

  el.documentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await addDocument(new FormData(el.documentForm));
  });

  document.body.addEventListener("click", async (event) => {
    const previewButton = event.target.closest("[data-preview-id]");
    const deleteButton = event.target.closest("[data-delete-id]");
    if (previewButton) previewDocument(previewButton.dataset.previewId);
    if (deleteButton) await deleteDocument(deleteButton.dataset.deleteId);
  });

  el.closePreview.addEventListener("click", () => el.previewDialog.close());
  el.previewDialog.addEventListener("close", () => {
    el.previewFrame.innerHTML = "";
  });
}

async function boot() {
  el.visitDate.valueAsDate = new Date();
  wireEvents();
  await refresh();

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => undefined);
  }
}

boot().catch((error) => {
  console.error(error);
  el.storageStatus.textContent = "Backend unavailable";
});
