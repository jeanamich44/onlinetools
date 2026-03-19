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
        if (timeSinceLast < 3000) {
            // Trop tôt, on attend le reliquat du sleep de 3 secondes
            setTimeout(debouncedCalculate, 3000 - timeSinceLast);
            return;
        }

        calculatePrice();
    }, 500);

    async function calculatePrice() {
        const form = document.querySelector('form');
        if (!form) return;

        isCalculating = true;
        const btn = document.getElementById(config.btnSubmit);
        if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
            const span = btn.querySelector('span');
            const statusText = 'Calcul du prix...';
            if (span) span.textContent = statusText;
            else btn.textContent = statusText;
        }

        // Détection flexible des champs
        const weight = form.querySelector('[name="packageWeight"]')?.value || form.querySelector('[name="weight"]')?.value;
        const senderCP = form.querySelector('[name="senderCP"]')?.value || form.querySelector('[name="sender_zip"]')?.value;
        const senderCity = form.querySelector('[name="senderCity"]')?.value || form.querySelector('[name="sender_city"]')?.value || 'PARIS';
        const receiverCP = form.querySelector('[name="receiverCP"]')?.value || form.querySelector('[name="recipient_zip"]')?.value;
        const receiverCity = form.querySelector('[name="receiverCity"]')?.value || form.querySelector('[name="recipient_city"]')?.value || 'VILLE';
        const receiverCountry = form.querySelector('[name="receiverCountry"]')?.value || 
                               form.querySelector('[name="destinationCountry"]')?.value || 
                               form.querySelector('[name="recipient_country"]')?.value || 
                               form.querySelector('[name="recipient_iso"]')?.value;

        // Dimensions (Crucial pour Express)
        const length = form.querySelector('[name="packageLength"]')?.value || form.querySelector('[name="length"]')?.value;
        const width = form.querySelector('[name="packageWidth"]')?.value || form.querySelector('[name="width"]')?.value;
        const height = form.querySelector('[name="packageHeight"]')?.value || form.querySelector('[name="height"]')?.value;

        const labelLower = config.offerLabel.toLowerCase();
        const isExpress = labelLower.includes('express');
        const isRelaisEurope = labelLower.includes('relais') && receiverCountry !== 'FR';
        const dimsRequired = isExpress || isRelaisEurope;

        // Conditions minimales pour simuler
        // Pour Express et Relais Europe, on exige aussi les dimensions
        if (!weight || !receiverCP || (dimsRequired && (!length || !width || !height))) {
            if (btn) {
                const labelElement = btn.querySelector('span') || btn;
                labelElement.textContent = dimsRequired && (!length || !width || !height) ? 'Dimensions requises...' : 'Veuillez remplir les champs...';
            }
            isCalculating = false;
            lastRequestCompleteTime = Date.now();
            return;
        }

        try {
            const data = {
                sender_iso: 'FR',
                sender_zip: senderCP || '75001',
                sender_city: senderCity,
                recipient_iso: receiverCountry || 'FR',
                recipient_zip: receiverCP,
                recipient_city: receiverCity,
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
                    updateButton(offer.price);
                    if (btn) {
                        btn.disabled = false;
                        btn.style.opacity = '1';
                        btn.style.cursor = 'pointer';
                    }
                } else {
                    if (btn) {
                        const label = btn.querySelector('span') || btn;
                        label.textContent = 'Service non disponible';
                    }
                }
            }
        } catch (err) {
            console.error("Erreur simulation:", err);
            if (btn) {
                const label = btn.querySelector('span') || btn;
                label.textContent = 'Indisponible (Réessayez)';
            }
        } finally {
            isCalculating = false;
            lastRequestCompleteTime = Date.now();
            
            // Si une requête a été mise en attente pendant le calcul actuel
            if (nextRequestQueued) {
                nextRequestQueued = false;
                setTimeout(debouncedCalculate, 3000); // On force le sleep de 3s demandé
            }
        }
    }

    function updateButton(price) {
        const btn = document.getElementById(config.btnSubmit);
        if (btn) {
            const span = btn.querySelector('span');
            const text = `Valider et Payer le Bordereau (${price.toFixed(2)}€)`;
            if (span) span.textContent = text;
            else btn.textContent = text;
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
            'receiverCountry', 'recipient_iso'
        ];
        
        watchFields.forEach(name => {
            const field = form.querySelector(`[name="${name}"]`);
            if (field) {
                field.addEventListener('input', debouncedCalculate);
                field.addEventListener('change', debouncedCalculate);
            }
        });

        // Premier calcul
        debouncedCalculate();
    });

})();
