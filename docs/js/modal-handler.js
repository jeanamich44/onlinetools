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
    
    modalMessage.textContent = `Votre ${fileName} a été généré avec succès. Cliquez ci-dessous pour le télécharger (un seul téléchargement possible).`;
    
    if (ref) {
        downloadBtn.style.display = "inline-block";
        downloadBtn.href = `${API_BASE}/api/download-pdf/${ref}`;
        downloadBtn.onclick = () => {
             setTimeout(() => {
                 closeModal();
             }, 1500);
        };
    } else {
        downloadBtn.style.display = "none";
    }
    
    modal.style.display = "flex";
}

function closeModal() {
    const modal = document.getElementById("successModal");
    if (modal) modal.style.display = "none";
    window.location.reload();
}
