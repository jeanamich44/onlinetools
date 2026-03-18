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

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    let currentCalculatedPrice = 1.0;
    const debouncedCalculate = debounce(calculatePrice, 500);

    async function calculatePrice() {
        const form = document.querySelector('form');
        if (!form) return;

        const btn = document.getElementById(config.btnSubmit);
        if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
            const span = btn.querySelector('span');
            if (span) span.textContent = 'Calcul du prix...';
            else btn.textContent = 'Calcul du prix...';
        }

        // Détection flexible des champs
        const weight = form.querySelector('[name="packageWeight"]')?.value || form.querySelector('[name="weight"]')?.value;
        const senderCP = form.querySelector('[name="senderCP"]')?.value || form.querySelector('[name="sender_zip"]')?.value;
        const senderCity = form.querySelector('[name="senderCity"]')?.value || form.querySelector('[name="sender_city"]')?.value || 'PARIS';
        const receiverCP = form.querySelector('[name="receiverCP"]')?.value || form.querySelector('[name="recipient_zip"]')?.value;
        const receiverCity = form.querySelector('[name="receiverCity"]')?.value || form.querySelector('[name="recipient_city"]')?.value || 'VILLE';
        const receiverCountry = form.querySelector('[name="receiverCountry"]')?.value || form.querySelector('[name="recipient_iso"]')?.value;

        // Conditions minimales pour simuler
        if (!weight || !receiverCP) {
            if (btn) {
                const label = btn.querySelector('span') || btn;
                label.textContent = 'Veuillez remplir les champs...';
            }
            return;
        }

        try {
            const data = {
                sender_iso: 'FR',
                sender_zip: senderCP || '75001',
                sender_city: senderCity,
                recipient_iso: receiverCountry,
                recipient_zip: receiverCP,
                recipient_city: receiverCity,
                weight: parseFloat(weight)
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
                
                // Trouver l'offre qui correspond au label
                const offer = result.offers.find(o => {
                    const label = o.label.toLowerCase().replace(/\s+/g, '');
                    return label.includes(target) || target.includes(label);
                });
                
                if (offer) {
                    currentCalculatedPrice = offer.price;
                    updateButton(currentCalculatedPrice);
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
        }
    }

    function updateButton(price) {
        const btn = document.getElementById(config.btnSubmit);
        if (btn) {
            const span = btn.querySelector('span');
            if (span) {
                span.textContent = `Valider et Payer le Bordereau (${price.toFixed(2)}€)`;
            } else {
                btn.textContent = `Valider et Payer le Bordereau (${price.toFixed(2)}€)`;
            }
        }
    }

    // Écouter les changements
    document.addEventListener('DOMContentLoaded', () => {
        const form = document.querySelector('form');
        if (!form) return;

        const watchFields = [
            'packageWeight', 'weight',
            'senderCP', 'sender_zip',
            'senderCity', 'sender_city',
            'receiverCP', 'recipient_zip',
            'receiverCity', 'recipient_city',
            'receiverCountry', 'recipient_iso'
        ];
        watchFields.forEach(name => {
            const field = form.querySelector(`[name="${name}"]`);
            if (field) {
                field.addEventListener('change', calculatePrice);
                field.addEventListener('input', debouncedCalculate); // Pour plus de réactivité sans spam
            }
        });

        // Premier calcul si déjà rempli (ex: session storage)
        setTimeout(calculatePrice, 500);
    });

})();
