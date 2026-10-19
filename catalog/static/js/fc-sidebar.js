
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
