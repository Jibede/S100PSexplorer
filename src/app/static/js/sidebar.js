document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("search");
    const listItems = document.querySelectorAll(".side-list li");
    const scrollContainer = document.querySelector(".side-list");

    // Mantém a posição do scroll
    const savedScroll = sessionStorage.getItem("sidebarScrollPosition");
    if (savedScroll && scrollContainer) {
        scrollContainer.scrollTop = savedScroll;
    }

    if (scrollContainer) {
        scrollContainer.addEventListener("scroll", () => {
            sessionStorage.setItem("sidebarScrollPosition", scrollContainer.scrollTop);
        });
    }

    // Lógica de filtro da barra de busca
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            const filter = e.target.value.toLowerCase();

            listItems.forEach((li) => {
                const text = li.textContent.toLowerCase();
                if (text.includes(filter)) {
                    li.style.display = "flex";
                } else {
                    li.style.display = "none";
                }
            });
        });
    }
});