document.addEventListener("DOMContentLoaded", () => {

  const exportModal = document.getElementById("exportModal");
  const exportOverlay = document.getElementById("modalOverlay");
  const closeBtn = document.getElementById("closeExportModalBtn");
  const exportForm = document.getElementById("exportForm");
  const statusDiv = document.getElementById("exportStatus");
  const openBtn = document.getElementById("openExportBtn");

  const selectAllCheckbox = document.getElementById("selectAll");
  const fileCheckboxes = document.querySelectorAll(".file-checkbox");

  if (openBtn) {
    openBtn.addEventListener("click", () => {
      exportModal.style.display = "block";
      exportOverlay.style.display = "block";
      if (statusDiv) statusDiv.textContent = "";
    });
  }

  const closeModal = () => {
    exportModal.style.display = "none";
    exportOverlay.style.display = "none";
  };

  if (closeBtn) closeBtn.addEventListener("click", closeModal);
  if (exportOverlay) exportOverlay.addEventListener("click", closeModal);

  selectAllCheckbox.addEventListener("change", () => {
    fileCheckboxes.forEach((checkbox) => {
      checkbox.checked = selectAllCheckbox.checked;
    });
  });

  fileCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      if (!checkbox.checked) {
        selectAllCheckbox.checked = false;
      } else {
        const allChecked = Array.from(fileCheckboxes).every((c) => c.checked);
        selectAllCheckbox.checked = allChecked;
      }
    });
  });

  if (exportForm) {
    exportForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const dataToSave = new FormData(exportForm);

      if (dataToSave.getAll("files_to_export").length === 0) {
        if (statusDiv) {
          statusDiv.innerHTML = `<span style="color: red;">Please select at least one file.</span>`;
        }
        return;
      }

      if (statusDiv) {
        statusDiv.innerHTML = "Processing in progress ...";
        statusDiv.classList.add("show");
      }

      try {
        const response = await fetch("/export_rules", {
          method: "POST",
          body: dataToSave,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Unknown server error");
        }

        const blob = await response.blob();
        
        const downloadUrl = window.URL.createObjectURL(blob);
        
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = "exported_files.zip";
        
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        if (statusDiv) {
          statusDiv.innerHTML = `<span style="color: var(--teal);">FILES EXPORTED SUCCESSFULLY</span>`;
          setTimeout(() => {
            closeModal();
          }, 1000);
        }

      } catch (error) {
        console.error("Error in request: ", error);
        alert("Error to export files: " + error.message);

        if (statusDiv) statusDiv.innerHTML = "";
      }
    });
  }
});