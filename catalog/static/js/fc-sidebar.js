
document.addEventListener("DOMContentLoaded", () => {
    const sidebarLinks = document.querySelectorAll(
        ".fc-page .sidebar a"
    );

    const navLinks = document.querySelectorAll(
        ".fc-page .top-nav a"
    );

    function updateSelection() {
        const currentHash = window.location.hash;

        sidebarLinks.forEach(link => {
            const selected =
                currentHash !== "" &&
                link.hash === currentHash;

            link.classList.toggle("is-selected", selected);

            if (selected) {
                link.setAttribute("aria-current", "location");
            } else {
                link.removeAttribute("aria-current");
            }
        });

        navLinks.forEach(link => {
            const selected =
                currentHash !== "" &&
                link.hash === currentHash;

            link.classList.toggle("is-selected", selected);

            if (selected) {
                link.setAttribute("aria-current", "location");
            } else {
                link.removeAttribute("aria-current");
            }
        });
    }

    window.addEventListener("hashchange", updateSelection);
    updateSelection();
});
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".sidebar-toggle").forEach((toggle) => {
        const list = document.getElementById(
            toggle.getAttribute("aria-controls")
        );
        if (!list) return;
        function toggleCategory() {
            list.hidden = !list.hidden;
            const isOpen = !list.hidden;
            toggle.setAttribute("aria-expanded", String(isOpen));
            toggle.querySelector(".toggle-icon").textContent = isOpen ? "−" : "+";
        }
        toggle.addEventListener("click", toggleCategory);
        toggle.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                toggleCategory();
            }
        });
    });
});

document.querySelectorAll('.top-nav a[href^="#"]').forEach(link => {
    link.addEventListener('click', () => {
        const targetId = link.getAttribute('href').slice(1);
        const categories = [
            { prefix: 'f_letter_', id: 'sidebar-features' },
            { prefix: 'i_letter_', id: 'sidebar-informations' },
            { prefix: 'asso_letter_', id: 'sidebar-associations' },
            { prefix: 'a_letter_', id: 'sidebar-attributes' },
            { prefix: 'role_letter_', id: 'sidebar-roles' }
        ];
        const category = categories.find(item =>
            targetId.startsWith(item.prefix)
        );
        if (!category) return;
        const list = document.getElementById(category.id);
        const toggle = document.querySelector(
            `[aria-controls="${category.id}"]`
        );
        if (!list || !toggle) return;
        if (list.hidden) {
            toggle.click();
        }
        const letter = targetId.slice(category.prefix.length);
        const sidebarLink = Array.from(
            list.querySelectorAll('.sidebar-letter a')
        ).find(a => a.textContent.trim() === letter);
        if (sidebarLink) {
            sidebarLink.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    });
});