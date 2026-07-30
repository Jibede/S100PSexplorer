document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById("search");
    const listItems = document.querySelectorAll(".side-list li");
    const scrollContainer = document.querySelector(".side-list"); 
    const itemAtivo = document.querySelector(".sidebar li.active");

    if (itemAtivo) {
        const dropdownPai = itemAtivo.closest("details");
        if (dropdownPai) {
            dropdownPai.setAttribute("open", "");
        }
        
        itemAtivo.scrollIntoView({ behavior: "instant", block: "nearest" });
    }

    const savedScroll = sessionStorage.getItem("sidebarScrollPosition");
    if (savedScroll && scrollContainer) {
        scrollContainer.scrollTop = savedScroll;
    }

    if (scrollContainer) {
        scrollContainer.addEventListener("scroll", () => {
            sessionStorage.setItem("sidebarScrollPosition", scrollContainer.scrollTop);
        });
    }

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