document.addEventListener('DOMContentLoaded', () => {
    // Récupération des éléments du DOM
    const exportModal = document.getElementById('exportModal');
    const exportOverlay = document.getElementById('modalOverlay');
    const closeBtn = document.getElementById('closeExportModalBtn');
    const exportForm = document.getElementById('exportForm');
    const statusDiv = document.getElementById('exportStatus');
    
    const openBtn = document.getElementById('openExportBtn');

    if (openBtn) {
        openBtn.addEventListener('click', () => {
            exportModal.style.display = 'block';
            exportOverlay.style.display = 'block';
            statusDiv.textContent = ''; // On réinitialise le statut à l'ouverture
        });
    }

    const closeModal = () => {
        exportModal.style.display = 'none';
        exportOverlay.style.display = 'none';
    };

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (exportOverlay) exportOverlay.addEventListener('click', closeModal);

})