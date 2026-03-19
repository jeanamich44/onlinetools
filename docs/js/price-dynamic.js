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
    let nextRequestQueued = false;
    let lastRequestCompleteTime = 0;

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    const debouncedCalculate = debounce(function() {
        if (isCalculating) {
            nextRequestQueued = true;
            return;
        }
        
        const now = Date.now();
        const timeSinceLast = now - lastRequestCompleteTime;
        if (timeSinceLast < 2000) { // Changement 3s -> 2s
            setTimeout(debouncedCalculate, 2000 - timeSinceLast);
            return;
        }

        calculatePrice();
    }, 500);

    async function calculatePrice() {
        const form = document.querySelector('form');
        if (!form) return;

        const btn = document.getElementById(config.btnSubmit);
        const updateStatus = (text) => {
            if (!btn) return;
            const span = btn.querySelector('span');
            if (span) span.textContent = text;
            else btn.textContent = text;
        };

        // Détection flexible des champs
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

        // --- Logique du message dynamique du bouton ---
        if (!weight && !receiverCP && !receiverCountry) {
            updateStatus('Remplir informations...');
        } else if (!weight) {
            updateStatus('Poids requis...');
        } else if (!receiverCP || !receiverCountry) {
            updateStatus('Destination requise...');
        } else if (dimsRequired && (!length || !width || !height)) {
            updateStatus('Dimensions requises...');
        } else {
            // Toutes les infos sont là, on peut calculer
            if (isCalculating) return; // Déjà en cours
            
            isCalculating = true;
            if (btn) {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
                updateStatus('Calcul du prix...');
            }

            try {
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
                        const originalBtnText = `Valider et Payer le Bordereau (${offer.price.toFixed(2)}€)`;
                        updateStatus(originalBtnText);
                        if (btn) {
                            btn.disabled = false;
                            btn.style.opacity = '1';
                            btn.style.cursor = 'pointer';
                        }
                    } else {
                        updateStatus('Service non disponible');
                    }
                }
            } catch (err) {
                console.error("Erreur simulation:", err);
                updateStatus('Indisponible (Réessayez)');
            } finally {
                isCalculating = false;
                lastRequestCompleteTime = Date.now();
                if (nextRequestQueued) {
                    nextRequestQueued = false;
                    setTimeout(debouncedCalculate, 2000);
                }
            }
            return;
        }

        // Si on est dans un cas où il manque des infos, on s'assure que le bouton reste bloqué
        if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        }
        isCalculating = false;
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
                field.addEventListener('input', debouncedCalculate);
                field.addEventListener('change', debouncedCalculate);
            }
        });

        // Premier calcul / mise à jour du bouton
        calculatePrice();
    });

})();
