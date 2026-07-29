  document.addEventListener("DOMContentLoaded", () => {
    const themeLinks = document.querySelectorAll(".change-theme");
    const themeStylesheet = document.getElementById("theme-stylesheet");
    const dropdownTrigger = document.querySelector(".dropdown-trigger");
    const dropdownMenu = document.querySelector(".dropdown-menu");

    themeLinks.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();

        const newThemeFile = link.getAttribute("data-theme");
        themeStylesheet.href = `/static/css/${newThemeFile}`;

        dropdownTrigger.textContent = link.textContent + " ▾";

        dropdownMenu.style.display = "none";

        setTimeout(() => {
          dropdownMenu.style.display = "";
        }, 100);
      });
    });
  });