/**
 * price-dynamic.js
 * Gère le calcul dynamique du prix sur les formulaires de service
 */

(function() {
    const config = {
        carrier: window.PRICE_CONFIG?.carrier || 'chronopost',
        offerLabel: window.PRICE_CONFIG?.offerLabel || 'Chrono 10',
        apiSimulate: 'https://transporteur.up.railway.app/api/' + (window.PRICE_CONFIG?.carrier || 'chronopost') + '/simulate',
        btnSubmit: 'btn-pay-submit',
        priceStore: 'calculatedPrice'
    };

    let isCalculating = false;
    let waitTimeout = null;

    // Fonction de mise à jour du statut visuel du bouton
    function updateStatus(text, isDisabled = true) {
        const btn = document.getElementById(config.btnSubmit);
        if (!btn) return;
        
        const span = btn.querySelector('span');
        if (span) span.textContent = text;
        else btn.textContent = text;

        if (isDisabled) {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        } else {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }
    }

    // Vérifie ce qu'il manque pour le calcul
    function getMissingInfo() {
        const form = document.querySelector('form');
        if (!form) return 'Formulaire introuvable';

        const weight = form.querySelector('[name="packageWeight"]')?.value || form.querySelector('[name="weight"]')?.value;
        const receiverCP = form.querySelector('[name="receiverCP"]')?.value || form.querySelector('[name="recipient_zip"]')?.value;
        const receiverCountry = form.querySelector('[name="receiverCountry"]')?.value || 
                               form.querySelector('[name="destinationCountry"]')?.value || 
                               form.querySelector('[name="recipient_country"]')?.value || 
                               form.querySelector('[name="recipient_iso"]')?.value;

        // Dimensions
        const length = form.querySelector('[name="packageLength"]')?.value || form.querySelector('[name="length"]')?.value;
        const width = form.querySelector('[name="packageWidth"]')?.value || form.querySelector('[name="width"]')?.value;
        const height = form.querySelector('[name="packageHeight"]')?.value || form.querySelector('[name="height"]')?.value;

        const labelLower = config.offerLabel.toLowerCase();
        const isExpress = labelLower.includes('express');
        const isRelaisEurope = labelLower.includes('relais') && (receiverCountry && receiverCountry !== 'FR');
        const dimsRequired = isExpress || isRelaisEurope;

        if (!weight && !receiverCP && !receiverCountry) return 'Remplir informations...';
        if (!weight) return 'Poids requis...';
        if (!receiverCP || !receiverCountry) return 'Destination requise...';
        if (dimsRequired && (!length || !width || !height)) return 'Dimensions requises...';

        return null; // Rien ne manque
    }

    // Fonction de regroupement des modifications (Batching 4s)
    function onFieldChange() {
        if (waitTimeout) clearTimeout(waitTimeout);

        const missing = getMissingInfo();
        if (missing) {
            // S'il manque des infos, on affiche juste le message sans lancer le timer "En calcul"
            updateStatus(missing, true);
        } else {
            // Tout est rempli, on peut passer en mode "En calcul..."
            updateStatus('En calcul...', true);
            waitTimeout = setTimeout(() => {
                calculatePrice();
            }, 4000);
        }
    }

    async function calculatePrice() {
        if (isCalculating) return;

        const missing = getMissingInfo();
        if (missing) {
            updateStatus(missing, true);
            return;
        }

        const form = document.querySelector('form');
        if (!form) return;

        isCalculating = true;
        updateStatus('Calcul via API...', true);

        try {
            const weight = form.querySelector('[name="packageWeight"]')?.value || form.querySelector('[name="weight"]')?.value;
            const receiverCP = form.querySelector('[name="receiverCP"]')?.value || form.querySelector('[name="recipient_zip"]')?.value;
            const receiverCountry = form.querySelector('[name="receiverCountry"]')?.value || 
                               form.querySelector('[name="destinationCountry"]')?.value || 
                               form.querySelector('[name="recipient_country"]')?.value || 
                               form.querySelector('[name="recipient_iso"]')?.value;
            const length = form.querySelector('[name="packageLength"]')?.value || form.querySelector('[name="length"]')?.value;
            const width = form.querySelector('[name="packageWidth"]')?.value || form.querySelector('[name="width"]')?.value;
            const height = form.querySelector('[name="packageHeight"]')?.value || form.querySelector('[name="height"]')?.value;

            const data = {
                sender_iso: 'FR',
                sender_zip: (form.querySelector('[name="senderCP"]')?.value || form.querySelector('[name="sender_zip"]')?.value) || '75001',
                sender_city: (form.querySelector('[name="senderCity"]')?.value || form.querySelector('[name="sender_city"]')?.value) || 'PARIS',
                recipient_iso: receiverCountry || 'FR',
                recipient_zip: receiverCP,
                recipient_city: (form.querySelector('[name="receiverCity"]')?.value || form.querySelector('[name="recipient_city"]')?.value) || 'VILLE',
                weight: parseFloat(weight),
                length: length ? parseFloat(length) : 0,
                width: width ? parseFloat(width) : 0,
                height: height ? parseFloat(height) : 0
            };

            const response = await fetch(config.apiSimulate, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) throw new Error("API Error");

            const result = await response.json();
            if (result.status === 'success' && result.offers) {
                const target = config.offerLabel.toLowerCase().replace(/\s+/g, '');
                const offer = result.offers.find(o => {
                    const label = o.label.toLowerCase().replace(/\s+/g, '');
                    return label.includes(target) || target.includes(label);
                });
                
                if (offer) {
                    updateStatus(`Valider et Payer le Bordereau (${offer.price.toFixed(2)}€)`, false);
                } else {
                    updateStatus('Service non disponible', true);
                }
            } else {
                throw new Error("Invalid result");
            }
        } catch (err) {
            console.error("Erreur simulation:", err);
            // On active le bouton pour que le client puisse cliquer sur "Réessayez"
            updateStatus('Indisponible (Réessayez)', false);
            
            // On ajoute un listener temporaire pour le retry au clic
            const btn = document.getElementById(config.btnSubmit);
            if (btn) {
                const retryHandler = () => {
                    btn.removeEventListener('click', retryHandler);
                    calculatePrice();
                };
                btn.addEventListener('click', retryHandler, { once: true });
            }
        } finally {
            isCalculating = false;
        }
    }

    // Écouter les changements
    document.addEventListener('DOMContentLoaded', () => {
        const form = document.querySelector('form');
        if (!form) return;

        const watchFields = [
            'packageWeight', 'weight',
            'packageLength', 'length',
            'packageWidth', 'width',
            'packageHeight', 'height',
            'senderCP', 'sender_zip',
            'senderCity', 'sender_city',
            'receiverCP', 'recipient_zip',
            'receiverCity', 'recipient_city',
            'receiverCountry', 'destinationCountry', 'recipient_country', 'recipient_iso'
        ];
        
        watchFields.forEach(name => {
            const field = form.querySelector(`[name="${name}"]`);
            if (field) {
                field.addEventListener('input', onFieldChange);
                field.addEventListener('change', onFieldChange);
            }
        });

        // Premier point d'entrée pour l'état du bouton
        onFieldChange();
    });

})();
