/**
 * Avsar — Base Application Script
 * Global accessible focus behavior, mobile navigation, and shared utilities.
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    // Auto-dismiss alerts after 6 seconds (if present)
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach((alert) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 6000);
    });

    // Close mobile navbar collapse upon clicking any nav-link
    const navLinks = document.querySelectorAll(".navbar-nav .nav-link");
    const navbarCollapse = document.getElementById("avsarNavbarNav");
    if (navbarCollapse) {
        navLinks.forEach((link) => {
            link.addEventListener("click", () => {
                if (navbarCollapse.classList.contains("show")) {
                    const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                    if (bsCollapse) bsCollapse.hide();
                }
            });
        });
    }
});
