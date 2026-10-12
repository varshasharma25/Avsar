/**
 * Avsar — Results Page Script
 * Interactive checklist, copy plan to clipboard, print triggering,
 * and device-only document cross-referencing.
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const btnCopyChecklist = document.getElementById("btn-copy-checklist");
    const btnPrint = document.getElementById("btn-print");
    const checkboxes = document.querySelectorAll(".action-checkbox");

    // Checklist interactive toggle
    checkboxes.forEach((cb) => {
        cb.addEventListener("change", () => {
            const label = cb.closest(".action-checklist-item");
            if (label) {
                if (cb.checked) {
                    label.classList.add("completed");
                } else {
                    label.classList.remove("completed");
                }
            }
        });
    });

    // Copy Plan to Clipboard
    if (btnCopyChecklist) {
        btnCopyChecklist.addEventListener("click", () => {
            const items = document.querySelectorAll(".action-checklist-item span");
            if (items.length === 0) return;

            const lines = ["AVSAR ACTION PLAN:"];
            items.forEach((item) => {
                lines.push(`[ ] ${item.textContent.trim()}`);
            });

            navigator.clipboard.writeText(lines.join("\n")).then(() => {
                const originalHtml = btnCopyChecklist.innerHTML;
                btnCopyChecklist.innerHTML = `<i class="bi bi-check2 text-success me-1" aria-hidden="true"></i> Copied!`;
                setTimeout(() => {
                    btnCopyChecklist.innerHTML = originalHtml;
                }, 2000);
            }).catch((err) => {
                console.error("Clipboard copy failed:", err);
            });
        });
    }

    // Print analysis
    if (btnPrint) {
        btnPrint.addEventListener("click", () => {
            window.print();
        });
    }

    // Cross-reference with User's Device Documents (from LocalStorage)
    checkDeviceDocumentsMatch();

    function checkDeviceDocumentsMatch() {
        const STORAGE_KEY = "avsar_device_documents";
        let deviceDocs = [];
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (raw) deviceDocs = JSON.parse(raw);
        } catch {
            return;
        }

        if (!Array.isArray(deviceDocs) || deviceDocs.length === 0) return;

        const docItems = document.querySelectorAll(".results-required-doc");
        docItems.forEach((item) => {
            const reqName = (item.getAttribute("data-doc-name") || "").toLowerCase();
            const badge = item.querySelector(".device-doc-match-badge");
            if (!badge) return;

            // Simple fuzzy token match against user's device doc names & categories
            const match = deviceDocs.find((d) => {
                const name = (d.name || "").toLowerCase();
                const cat = (d.category || "").toLowerCase();

                // Common document keywords
                const keywords = ["marksheet", "income", "caste", "domicile", "aadhaar", "id", "photo", "certificate", "pass", "resume", "cv"];
                for (const kw of keywords) {
                    if (reqName.includes(kw) && (name.includes(kw) || cat.includes(kw))) {
                        return true;
                    }
                }
                return reqName.includes(name) || name.includes(reqName);
            });

            if (match) {
                badge.className = "device-doc-match-badge badge bg-success-subtle text-success border border-success-subtle";
                badge.style.fontSize = "0.72rem";
                badge.innerHTML = `<i class="bi bi-shield-check me-1"></i> On your device: ${escapeHtml(match.name)}`;
                badge.classList.remove("d-none");
            }
        });
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
});
