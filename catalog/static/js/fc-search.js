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

const clearSearchButton = document.getElementById('catalog-search-clear');
const searchInput = document.getElementById('catalog-search');

if (clearSearchButton && searchInput) {
    const updateClearButton = () => {
        clearSearchButton.hidden = searchInput.value.length === 0;
    };

    searchInput.addEventListener('input', updateClearButton);

    clearSearchButton.addEventListener('click', () => {
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input', { bubbles: true }));
        searchInput.focus();
    });

    updateClearButton();
}