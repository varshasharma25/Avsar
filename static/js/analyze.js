/**
 * Avsar — Analyze Opportunity Script
 * Form validation, character counter, sample loader, submission to Flask API,
 * ephemeral in-memory notice file extractor, and private device document locker.
 *
 * Privacy Guarantee:
 * - Notice files uploaded for analysis are extracted in-memory and never saved to disk.
 * - Personal documents added to "My Device Documents" are saved strictly in the
 *   user's local browser storage (localStorage). No other device or user can access them.
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    // --- Form & Input Elements ---
    const form = document.getElementById("opportunity-form");
    const formCard = document.getElementById("form-card");
    const noticeText = document.getElementById("notice-text");
    const charCounter = document.getElementById("char-counter");
    const categorySelect = document.getElementById("notice-category");
    const noticeError = document.getElementById("notice-error");
    const btnAnalyze = document.getElementById("btn-analyze");
    const btnClear = document.getElementById("btn-clear");
    const btnLoadSample = document.getElementById("btn-load-sample");
    const btnRetry = document.getElementById("btn-retry");

    // --- State Containers ---
    const stateLoading = document.getElementById("state-loading");
    const stateError = document.getElementById("state-error");
    const errorMessageText = document.getElementById("error-message-text");

    // --- Notice File Upload Elements ---
    const btnUploadNotice = document.getElementById("btn-upload-notice");
    const noticeFileInput = document.getElementById("notice-file-input");
    const noticeFileStatus = document.getElementById("notice-file-status");
    const noticeFileStatusText = document.getElementById("notice-file-status-text");

    // --- Device Documents Locker Elements ---
    const deviceDocInput = document.getElementById("device-doc-input");
    const btnAddDeviceDoc = document.getElementById("btn-add-device-doc");
    const addDocDrawer = document.getElementById("add-doc-drawer");
    const docFileName = document.getElementById("doc-file-name");
    const docTypeSelect = document.getElementById("doc-type-select");
    const btnSaveDoc = document.getElementById("btn-save-doc");
    const btnCancelDoc = document.getElementById("btn-cancel-doc");
    const deviceDocsEmpty = document.getElementById("device-docs-empty");
    const deviceDocsList = document.getElementById("device-docs-list");
    const deviceDocsSyncBar = document.getElementById("device-docs-sync-bar");
    const deviceDocsCountText = document.getElementById("device-docs-count-text");
    const btnSyncProfile = document.getElementById("btn-sync-profile");

    const STORAGE_KEY = "avsar_device_documents";
    const MAX_CHARS = 20000;
    const MIN_CHARS = 30;

    let pendingDocFile = null;

    // --- High-Quality Sample Notice for Testing ---
    const SAMPLE_NOTICE = `GOVERNMENT OF INDIA - MINISTRY OF EDUCATION
NATIONAL MERIT-CUM-MEANS SCHOLARSHIP SCHEME (NMMSS) 2026-27

Applications are invited from meritorious students belonging to economically weaker sections.

1. OBJECTIVE & BENEFITS:
Selected candidates will receive financial assistance of ₹12,000/- per annum (₹1,000 per month) to support secondary and higher secondary education up to Class 12.

2. ELIGIBILITY CRITERIA:
- The candidate must be a regular student studying in Class 9 in a recognized government, government-aided, or local body school.
- Minimum 55% marks or equivalent grade in Class 8 examination (relaxable by 5% for SC/ST).
- Total parental annual income from all sources must not exceed ₹3,50,000/- per annum.
- Students enrolled in private schools, Kendriya Vidyalayas, or Navodaya Vidyalayas are NOT eligible.

3. REQUIRED DOCUMENTS:
- Class 8 marksheet / pass certificate
- Income certificate issued by competent revenue authority
- Caste certificate (if applicable)
- Domicile certificate
- Bank account details (Aadhaar linked)

4. APPLICATION PROCESS & KEY DATES:
- Online application submission starts: 01 October 2026
- Last date of registration: 30 November 2026
- State-level scholarship examination: 20 December 2026
- Application website: https://scholarships.gov.in (National Scholarship Portal)
- Selection is based on the National Merit Examination (MAT & SAT test).`;

    // -------------------------------------------------------------------------
    // Initialization
    // -------------------------------------------------------------------------

    if (noticeText && charCounter) {
        noticeText.addEventListener("input", updateCharCounter);
        updateCharCounter();
    }

    // Initialize Device Document Locker from LocalStorage
    renderDeviceDocuments();

    // -------------------------------------------------------------------------
    // Notice File Upload & Drag-and-Drop (In-Memory / Private)
    // -------------------------------------------------------------------------

    if (btnUploadNotice && noticeFileInput) {
        btnUploadNotice.addEventListener("click", () => {
            noticeFileInput.click();
        });

        noticeFileInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file) {
                handleNoticeFile(file);
            }
            noticeFileInput.value = "";
        });
    }

    // Drag-and-drop support on the textarea
    if (noticeText) {
        noticeText.addEventListener("dragover", (e) => {
            e.preventDefault();
            noticeText.classList.add("border-success");
        });

        noticeText.addEventListener("dragleave", (e) => {
            e.preventDefault();
            noticeText.classList.remove("border-success");
        });

        noticeText.addEventListener("drop", (e) => {
            e.preventDefault();
            noticeText.classList.remove("border-success");
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
                handleNoticeFile(e.dataTransfer.files[0]);
            }
        });
    }

    async function handleNoticeFile(file) {
        clearValidationError();
        const fname = file.name.toLowerCase();

        // 1. Text formats: Extract 100% on client-side
        if (fname.endsWith(".txt") || fname.endsWith(".md") || fname.endsWith(".csv") || fname.endsWith(".rtf") || fname.endsWith(".json")) {
            const reader = new FileReader();
            reader.onload = (evt) => {
                const text = (evt.target?.result || "").trim();
                if (text) {
                    noticeText.value = text.slice(0, MAX_CHARS);
                    updateCharCounter();
                    showFileNoticeStatus(`Loaded "${file.name}" (${noticeText.value.length.toLocaleString()} characters) directly on your device.`);
                } else {
                    showValidationError("The selected text file is empty.");
                }
            };
            reader.onerror = () => {
                showValidationError("Could not read text file from device.");
            };
            reader.readAsText(file);
            return;
        }

        // 2. PDF format: In-memory extraction via Flask endpoint
        if (fname.endsWith(".pdf")) {
            showFileNoticeStatus(`Reading "${file.name}" in memory...`);
            const formData = new FormData();
            formData.append("file", file);

            try {
                const res = await fetch("/api/extract-text", {
                    method: "POST",
                    body: formData
                });
                const data = await res.json();
                if (res.ok && data.text) {
                    noticeText.value = data.text;
                    updateCharCounter();
                    showFileNoticeStatus(`Loaded "${file.name}" (${data.text.length.toLocaleString()} characters) ephemerally in-memory.`);
                } else {
                    throw new Error(data.error || "Failed to extract text from PDF.");
                }
            } catch (err) {
                console.error("PDF extraction error:", err);
                hideFileNoticeStatus();
                showValidationError(err.message || "Failed to parse PDF document.");
            }
            return;
        }

        showValidationError("Please select a supported document: .pdf, .txt, or .md");
    }

    function showFileNoticeStatus(message) {
        if (noticeFileStatus && noticeFileStatusText) {
            noticeFileStatusText.textContent = message;
            noticeFileStatus.classList.remove("d-none");
        }
    }

    function hideFileNoticeStatus() {
        if (noticeFileStatus) {
            noticeFileStatus.classList.add("d-none");
        }
    }

    // -------------------------------------------------------------------------
    // Device Documents Locker (100% Private to Local Browser Storage)
    // -------------------------------------------------------------------------

    if (btnAddDeviceDoc && deviceDocInput) {
        btnAddDeviceDoc.addEventListener("click", () => {
            deviceDocInput.click();
        });

        deviceDocInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file) {
                pendingDocFile = file;
                if (docFileName) {
                    docFileName.textContent = `${file.name} (${formatBytes(file.size)})`;
                }
                if (addDocDrawer) {
                    addDocDrawer.classList.remove("d-none");
                }
            }
            deviceDocInput.value = "";
        });
    }

    if (btnCancelDoc && addDocDrawer) {
        btnCancelDoc.addEventListener("click", () => {
            pendingDocFile = null;
            addDocDrawer.classList.add("d-none");
        });
    }

    if (btnSaveDoc) {
        btnSaveDoc.addEventListener("click", () => {
            if (!pendingDocFile) return;

            const category = docTypeSelect ? docTypeSelect.value : "General Document";
            const newDoc = {
                id: "doc_" + Date.now(),
                name: pendingDocFile.name,
                category: category,
                size: formatBytes(pendingDocFile.size),
                dateAdded: new Date().toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
            };

            const existing = getStoredDeviceDocuments();
            existing.push(newDoc);
            saveStoredDeviceDocuments(existing);

            pendingDocFile = null;
            if (addDocDrawer) addDocDrawer.classList.add("d-none");
            renderDeviceDocuments();
        });
    }

    if (btnSyncProfile) {
        btnSyncProfile.addEventListener("click", () => {
            syncDocumentsToProfile(true);
        });
    }

    function getStoredDeviceDocuments() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch {
            return [];
        }
    }

    function saveStoredDeviceDocuments(docs) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(docs));
        } catch (e) {
            console.warn("Could not save to localStorage:", e);
        }
    }

    function deleteDeviceDocument(id) {
        const docs = getStoredDeviceDocuments().filter((d) => d.id !== id);
        saveStoredDeviceDocuments(docs);
        renderDeviceDocuments();
    }

    function renderDeviceDocuments() {
        const docs = getStoredDeviceDocuments();

        if (!deviceDocsEmpty || !deviceDocsList) return;

        if (docs.length === 0) {
            deviceDocsEmpty.classList.remove("d-none");
            deviceDocsList.classList.add("d-none");
            if (deviceDocsSyncBar) deviceDocsSyncBar.classList.add("d-none");
            return;
        }

        deviceDocsEmpty.classList.add("d-none");
        deviceDocsList.classList.remove("d-none");
        if (deviceDocsSyncBar) {
            deviceDocsSyncBar.classList.remove("d-none");
            if (deviceDocsCountText) {
                deviceDocsCountText.textContent = `${docs.length} ${docs.length === 1 ? 'document' : 'documents'} added`;
            }
        }

        deviceDocsList.innerHTML = "";

        docs.forEach((doc) => {
            const item = document.createElement("div");
            item.className = "device-doc-item";

            // Determine appropriate icon
            let iconClass = "bi-file-earmark-text";
            const lowerName = doc.name.toLowerCase();
            if (lowerName.endsWith(".pdf")) iconClass = "bi-file-earmark-pdf text-danger";
            else if (lowerName.endsWith(".doc") || lowerName.endsWith(".docx")) iconClass = "bi-file-earmark-word text-primary";
            else if (lowerName.endsWith(".png") || lowerName.endsWith(".jpg") || lowerName.endsWith(".jpeg")) iconClass = "bi-file-earmark-image text-success";

            item.innerHTML = `
                <div class="d-flex align-items-center gap-3 text-truncate">
                    <div class="device-doc-icon">
                        <i class="bi ${iconClass}" aria-hidden="true"></i>
                    </div>
                    <div class="text-truncate">
                        <div class="fw-semibold text-charcoal small text-truncate" title="${escapeHtml(doc.name)}">
                            ${escapeHtml(doc.name)}
                        </div>
                        <div class="d-flex align-items-center gap-2 flex-wrap">
                            <span class="badge bg-sage-tint text-success border border-success-subtle py-0 px-2" style="font-size: 0.72rem;">
                                ${escapeHtml(doc.category)}
                            </span>
                            <span class="text-muted" style="font-size: 0.75rem;">${escapeHtml(doc.size)} • Added ${escapeHtml(doc.dateAdded)}</span>
                        </div>
                    </div>
                </div>
                <div class="d-flex align-items-center gap-1 ms-2">
                    <button type="button" class="btn btn-sm btn-outline-danger border-0 p-1 px-2 btn-delete-doc" data-id="${doc.id}" title="Remove document">
                        <i class="bi bi-trash" aria-hidden="true"></i>
                        <span class="visually-hidden">Remove</span>
                    </button>
                </div>
            `;

            const btnDel = item.querySelector(".btn-delete-doc");
            if (btnDel) {
                btnDel.addEventListener("click", () => {
                    deleteDeviceDocument(doc.id);
                });
            }

            deviceDocsList.appendChild(item);
        });
    }

    function syncDocumentsToProfile(showToast = false) {
        const docs = getStoredDeviceDocuments();
        if (docs.length === 0) return;

        const skillsInput = document.getElementById("profile-skills");
        if (skillsInput) {
            const docSummary = docs.map((d) => `${d.name} (${d.category})`).join(", ");
            const prefix = "Documents: ";
            if (!skillsInput.value.includes(prefix)) {
                skillsInput.value = skillsInput.value ? `${skillsInput.value} | ${prefix}${docSummary}` : `${prefix}${docSummary}`;
            }

            // Expand accordion so user can inspect
            const accordionCollapse = document.getElementById("collapse-profile");
            if (accordionCollapse && !accordionCollapse.classList.contains("show")) {
                const bsCollapse = bootstrap.Collapse.getOrCreateInstance(accordionCollapse);
                bsCollapse.show();
            }

            if (showToast) {
                const count = docs.length;
                alert(`Synced ${count} device document ${count === 1 ? 'record' : 'records'} into your eligibility profile.`);
            }
        }
    }

    function formatBytes(bytes) {
        if (!bytes || bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    // -------------------------------------------------------------------------
    // General Form Handlers
    // -------------------------------------------------------------------------

    function updateCharCounter() {
        const length = noticeText.value.length;
        charCounter.textContent = `${length.toLocaleString()} / ${MAX_CHARS.toLocaleString()} chars`;
        if (length >= MAX_CHARS) {
            charCounter.classList.add("limit-reached");
        } else {
            charCounter.classList.remove("limit-reached");
        }
        clearValidationError();
    }

    if (btnLoadSample) {
        btnLoadSample.addEventListener("click", () => {
            loadSampleData();
        });
    }

    if (btnClear) {
        btnClear.addEventListener("click", () => {
            form.reset();
            updateCharCounter();
            clearValidationError();
            hideStates();
            hideFileNoticeStatus();
        });
    }

    if (btnRetry) {
        btnRetry.addEventListener("click", () => {
            submitForm();
        });
    }

    if (form) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            submitForm();
        });
    }

    function loadSampleData() {
        noticeText.value = SAMPLE_NOTICE;
        categorySelect.value = "scholarship";
        updateCharCounter();

        const edu = document.getElementById("profile-education");
        const status = document.getElementById("profile-course-year");
        const age = document.getElementById("profile-age");
        const state = document.getElementById("profile-state");
        const income = document.getElementById("profile-category-income");
        const skills = document.getElementById("profile-skills");

        if (edu) edu.value = "Class 8 Passed (62%)";
        if (status) status.value = "Class 9 Student in State Govt High School";
        if (age) age.value = "14";
        if (state) state.value = "Rajasthan";
        if (income) income.value = "Family income ₹ 2,10,000 per annum";
        if (skills) skills.value = "Math, Science basics";

        clearValidationError();
    }

    function clearValidationError() {
        noticeText.classList.remove("is-invalid");
        if (noticeError) {
            noticeError.classList.add("d-none");
            noticeError.textContent = "";
        }
    }

    function showValidationError(message) {
        noticeText.classList.add("is-invalid");
        if (noticeError) {
            noticeError.classList.remove("d-none");
            noticeError.textContent = message;
        }
        noticeText.focus();
    }

    function hideStates() {
        if (stateLoading) stateLoading.classList.add("d-none");
        if (stateError) stateError.classList.add("d-none");
        if (formCard) formCard.classList.remove("d-none");
    }

    async function submitForm() {
        const text = noticeText.value.trim();
        const category = categorySelect.value;

        if (!text) {
            showValidationError("Please paste the notice text or upload a file from your device.");
            return;
        }

        if (text.length < MIN_CHARS) {
            showValidationError(`Notice text is too short. Please paste or upload at least ${MIN_CHARS} characters.`);
            return;
        }

        if (text.length > MAX_CHARS) {
            showValidationError(`Notice text exceeds the maximum limit of ${MAX_CHARS.toLocaleString()} characters.`);
            return;
        }

        if (!category) {
            categorySelect.focus();
            showValidationError("Please select an opportunity category.");
            return;
        }

        clearValidationError();

        // Auto-sync available device documents into the profile payload
        syncDocumentsToProfile(false);

        // Show loading state, hide form card
        if (stateError) stateError.classList.add("d-none");
        if (stateLoading) stateLoading.classList.remove("d-none");
        if (formCard) formCard.classList.add("d-none");
        btnAnalyze.disabled = true;

        window.scrollTo({ top: 0, behavior: "smooth" });

        const deviceDocs = getStoredDeviceDocuments();

        const profile = {
            education: (document.getElementById("profile-education")?.value || "").trim(),
            course_year: (document.getElementById("profile-course-year")?.value || "").trim(),
            age: (document.getElementById("profile-age")?.value || "").trim(),
            state: (document.getElementById("profile-state")?.value || "").trim(),
            category_income: (document.getElementById("profile-category-income")?.value || "").trim(),
            skills: (document.getElementById("profile-skills")?.value || "").trim(),
            available_device_documents: deviceDocs.map((d) => `${d.name} (${d.category})`)
        };

        const language = document.querySelector('input[name="language"]:checked')?.value || "en";

        const payload = {
            notice_text: text,
            category: category,
            language: language,
            profile: profile
        };

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                const targetUrl = data.redirect || "/results";
                window.location.href = targetUrl;
            } else {
                throw new Error(data.error || `Server returned status ${response.status}`);
            }
        } catch (err) {
            console.error("Analysis request failed:", err);
            if (stateLoading) stateLoading.classList.add("d-none");
            if (formCard) formCard.classList.remove("d-none");
            if (stateError) {
                stateError.classList.remove("d-none");
                errorMessageText.textContent = err.message || "Failed to analyze notice. Please check your network and try again.";
            }
            btnAnalyze.disabled = false;
        }
    }
});
