document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("catalog-search");
    const resultsContainer = document.getElementById("catalog-search-results");

    if (!searchInput || !resultsContainer) {
        return;
    }

    const entries = Array.from(
        document.querySelectorAll(".fc-page .column h4[id]")
    );

    searchInput.addEventListener("input", () => {
        const query = searchInput.value.trim().toLowerCase();

        resultsContainer.replaceChildren();

        if (query === "") {
            return;
        }

        const matches = entries.filter(entry =>
            entry.textContent.toLowerCase().includes(query)
        );

        matches.forEach(entry => {
            const link = document.createElement("a");

            link.href = "#" + entry.id;
            link.textContent = entry.textContent;
            link.className = "search-result";

            resultsContainer.appendChild(link);
        });
    });
});