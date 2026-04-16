const modalHTML = `
  <div id="successModal" class="modal-overlay">
    <div class="modal-card">
      <span class="modal-icon">✅</span>
      <h2 class="modal-title">Paiement Validé !</h2>
      <p class="modal-body" id="modalMessage">Votre document a été généré avec succès. Vous pouvez le télécharger via le bouton ci-dessous (limite : 1 seul téléchargement).</p>
      <a id="downloadBtn" href="#" class="modal-btn">⬇️ Télécharger le PDF</a>
      <button onclick="closeModal()" class="modal-btn modal-btn-secondary">Fermer</button>
    </div>
  </div>`;

document.body.insertAdjacentHTML('beforeend', modalHTML);

function showSuccessModal(ref, productType) {
    const modal = document.getElementById("successModal");
    const downloadBtn = document.getElementById("downloadBtn");
    const modalMessage = document.getElementById("modalMessage");
    const API_BASE = "https://generate-docs-production.up.railway.app";
    
    let fileName = "Document";
    if (productType && productType.includes('rib')) {
        fileName = 'RIB';
    } else if (productType && productType.includes('facture')) {
        fileName = 'Facture';
    }
    
    modalMessage.textContent = `Votre ${fileName} est prêt ! Cliquez ici pour le télécharger (limite : 1 seul essai).`;
    
    if (ref) {
        downloadBtn.style.display = "inline-block";
        downloadBtn.href = `${API_BASE}/api/download-pdf/${ref}`;
        downloadBtn.onclick = () => {
             // On laisse le temps au téléchargement de démarrer
             setTimeout(() => {
                 closeModal(true);
             }, 1000);
        };
    } else {
        downloadBtn.style.display = "none";
    }
    
    modal.style.display = "block"; // Utilisation de block pour le toast

    // Auto-fermeture après 10 secondes
    setTimeout(() => {
        closeModal(false);
    }, 10000);
}

function closeModal(shouldReload = false) {
    const modal = document.getElementById("successModal");
    if (modal) {
        modal.style.display = "none";
        // On nettoie l'URL pour ne pas réafficher la pop-up au refresh manuel
        if (window.location.search.includes('checkout_reference')) {
            const newUrl = window.location.origin + window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        }
    }
    if (shouldReload) {
        window.location.reload();
    }
}
