const menuToggle = document.querySelector("[data-menu-toggle]");
const mobileNav = document.querySelector("[data-mobile-nav]");

if (menuToggle && mobileNav) {
    menuToggle.addEventListener("click", () => {
        mobileNav.classList.toggle("is-open");
    });
}

document.querySelectorAll("[data-flash-close]").forEach((button) => {
    button.addEventListener("click", () => {
        const flash = button.closest(".flash");
        if (flash) {
            flash.remove();
        }
    });
});

document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
        const targetId = button.dataset.target;
        const target = document.getElementById(targetId);
        if (!target) {
            return;
        }
        const nextType = target.type === "password" ? "text" : "password";
        target.type = nextType;
        button.textContent = nextType === "password" ? "Show" : "Hide";
    });
});

function isInteractiveElement(target) {
    return Boolean(target.closest("a, button, input, select, textarea, label, form"));
}

document.querySelectorAll("[data-card-url]").forEach((card) => {
    card.addEventListener("click", (event) => {
        if (isInteractiveElement(event.target)) {
            return;
        }

        const url = card.dataset.cardUrl;
        if (url) {
            window.location.href = url;
        }
    });
});

const searchInput = document.querySelector("[data-course-search]");
const categoryFilter = document.querySelector("[data-category-filter]");
const courseItems = [...document.querySelectorAll("[data-course-item]")];
const visibleCourseCount = document.getElementById("visible-course-count");
const emptyCourses = document.querySelector("[data-empty-courses]");

function filterCourses() {
    if (!courseItems.length) {
        return;
    }

    const searchValue = (searchInput?.value || "").trim().toLowerCase();
    const categoryValue = categoryFilter?.value || "";

    let visibleItems = 0;

    courseItems.forEach((item) => {
        const matchesSearch = item.dataset.title.includes(searchValue);
        const matchesCategory = !categoryValue || item.dataset.category === categoryValue;
        const shouldShow = matchesSearch && matchesCategory;

        item.classList.toggle("hidden", !shouldShow);
        if (shouldShow) {
            visibleItems += 1;
        }
    });

    if (visibleCourseCount) {
        visibleCourseCount.textContent = String(visibleItems);
    }

    if (emptyCourses) {
        emptyCourses.classList.toggle("hidden", visibleItems !== 0);
    }
}

[searchInput, categoryFilter].forEach((field) => {
    if (field) {
        field.addEventListener("input", filterCourses);
        field.addEventListener("change", filterCourses);
    }
});

filterCourses();

function showToast(message, tone = "success") {
    let flashStack = document.querySelector(".flash-stack");

    if (!flashStack) {
        const container = document.querySelector(".page-main .container");
        if (!container) {
            return;
        }
        flashStack = document.createElement("div");
        flashStack.className = "flash-stack";
        container.prepend(flashStack);
    }

    const flash = document.createElement("div");
    flash.className = `flash flash-${tone}`;
    flash.innerHTML = `<span>${message}</span><button type="button" class="flash-close">x</button>`;
    flash.querySelector(".flash-close")?.addEventListener("click", () => flash.remove());
    flashStack.prepend(flash);

    window.setTimeout(() => flash.remove(), 3500);
}

document.querySelectorAll("[data-status-action]").forEach((button) => {
    button.addEventListener("click", async () => {
        const url = button.dataset.url;
        const action = button.dataset.statusAction;
        if (!url || !action) {
            return;
        }

        const actionRow = button.closest(".progress-actions");
        const actionButtons = actionRow ? [...actionRow.querySelectorAll("button")] : [button];
        actionButtons.forEach((item) => {
            item.disabled = true;
        });

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: JSON.stringify({ action }),
            });

            const payload = await response.json();
            if (!response.ok || !payload.ok) {
                throw new Error(payload.message || "Unable to update course status.");
            }

            const statusLabel = document.querySelector(`[data-status-label="${payload.course_id}"]`);
            if (statusLabel) {
                statusLabel.textContent = payload.status;
            }

            showToast("Course status updated.", "success");
        } catch (error) {
            showToast(error.message || "Unable to update course status.", "error");
        } finally {
            actionButtons.forEach((item) => {
                item.disabled = false;
            });
        }
    });
});

if ("IntersectionObserver" in window) {
    const counterObserver = new IntersectionObserver(
        (entries, observer) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                const counter = entry.target;
                const target = Number(counter.dataset.count || "0");
                if (!Number.isFinite(target) || target <= 0) {
                    observer.unobserve(counter);
                    return;
                }

                const duration = 900;
                const start = performance.now();

                const step = (now) => {
                    const progress = Math.min((now - start) / duration, 1);
                    const value = Math.round(target * progress);
                    counter.textContent = value.toLocaleString();
                    if (progress < 1) {
                        requestAnimationFrame(step);
                    }
                };

                requestAnimationFrame(step);
                observer.unobserve(counter);
            });
        },
        { threshold: 0.5 }
    );

    document.querySelectorAll("[data-count]").forEach((counter) => {
        counterObserver.observe(counter);
    });
}
