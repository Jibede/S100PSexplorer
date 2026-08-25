document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("uploadModal");
  const overlay = document.getElementById("modalOverlay"); // Récupération du fond noir
  const openBtn = document.getElementById("openModalBtn");
  const closeBtn = document.getElementById("closeModalBtn");
  const form = document.getElementById("uploadForm");
  const statusDiv = document.getElementById("uploadStatus");

  const closeModal = () => {
    modal.style.display = "none";
    overlay.style.display = "none";
    if (statusDiv) statusDiv.innerHTML = "";
    if (form) form.reset();
  };

  if (openBtn && modal && overlay) {
    openBtn.addEventListener("click", () => {
      modal.style.display = "block";
      overlay.style.display = "block";
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", closeModal);
  }

  if (overlay) {
    overlay.addEventListener("click", closeModal);
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (statusDiv) {
        statusDiv.innerHTML = "Processing in progess ...";
        statusDiv.classList.add("show");
      }

      const dataToSave = new FormData(form);

      fetch("/upload_file", {
        method: "POST",
        body: dataToSave,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.status == "sucess" || data.mesage) {
            if (statusDiv) {
              statusDiv.innerHTML = `<span style="color: var(--teal);">${data.message || "FILE SENT "}</span>`;
              setTimeout(() => {
                closeModal;
                window.location.reload()
              }, 1000);
            }
          } else {
            alert("Error to save: " + (data.error || "Unknown Error"));
            if (statusDiv) statusDiv.innerHTML = "";
          }
        })
        .catch((error) => {
          console.log("Error in requisition: ", error);
          alert("Error to upload file");

          if (statusDiv) statusDiv.innerHTML = "";
        });
    });
  }
});
