const menuToggle = document.querySelector("[data-menu-toggle]");
const mobileNav = document.querySelector("[data-mobile-nav]");
const themeToggle = document.querySelector("[data-theme-toggle]");
const themeLabel = document.querySelector("[data-theme-label]");
const rootElement = document.documentElement;

if (menuToggle && mobileNav) {
    menuToggle.addEventListener("click", () => {
        const isOpen = mobileNav.classList.toggle("is-open");
        menuToggle.setAttribute("aria-expanded", String(isOpen));
    });

    mobileNav.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            mobileNav.classList.remove("is-open");
            menuToggle.setAttribute("aria-expanded", "false");
        });
    });

    const desktopMenuMedia = window.matchMedia("(min-width: 1041px)");
    const resetMenuState = (event) => {
        if (event.matches) {
            mobileNav.classList.remove("is-open");
            menuToggle.setAttribute("aria-expanded", "false");
        }
    };

    if (typeof desktopMenuMedia.addEventListener === "function") {
        desktopMenuMedia.addEventListener("change", resetMenuState);
    } else if (typeof desktopMenuMedia.addListener === "function") {
        desktopMenuMedia.addListener(resetMenuState);
    }
}

function getActiveTheme() {
    return rootElement.dataset.theme === "dark" ? "dark" : "light";
}

function syncThemeControl() {
    const isDarkTheme = getActiveTheme() === "dark";

    if (themeToggle) {
        themeToggle.checked = isDarkTheme;
    }

    if (themeLabel) {
        themeLabel.textContent = isDarkTheme ? "Dark mode" : "Light mode";
    }
}

if (themeToggle) {
    syncThemeControl();

    themeToggle.addEventListener("change", () => {
        const nextTheme = themeToggle.checked ? "dark" : "light";
        rootElement.dataset.theme = nextTheme;

        try {
            localStorage.setItem("theme-preference", nextTheme);
        } catch (error) {
            console.warn("Theme preference could not be saved.", error);
        }

        syncThemeControl();
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
    const categoryValue = (categoryFilter?.value || "").trim().toLowerCase();

    let visibleItems = 0;

    courseItems.forEach((item) => {
        const searchContent = item.dataset.search || item.dataset.title || "";
        const matchesSearch = searchContent.includes(searchValue);
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
