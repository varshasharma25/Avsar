/**
 * Avsar — Opportunities Discovery Script
 * Interactive category filtering and pre-selection navigation.
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const filterButtons = document.querySelectorAll(".category-filter-nav .nav-link");
    const guideCards = document.querySelectorAll(".opportunity-guide-item");

    filterButtons.forEach((btn) => {
        btn.addEventListener("click", (e) => {
            const targetCat = btn.getAttribute("data-category");
            if (!targetCat) return;

            // Update active pill
            filterButtons.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");

            // Filter guide cards
            guideCards.forEach((card) => {
                const cardCat = card.getAttribute("data-category");
                if (targetCat === "all" || cardCat === targetCat) {
                    card.classList.remove("d-none");
                } else {
                    card.classList.add("d-none");
                }
            });
        });
    });
});
