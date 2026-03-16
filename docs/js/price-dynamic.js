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

    let currentCalculatedPrice = 1.0;

    async function calculatePrice() {
        const form = document.querySelector('form');
        if (!form) return;

        const weight = form.querySelector('[name="packageWeight"]')?.value;
        const senderCP = form.querySelector('[name="senderCP"]')?.value;
        const receiverCP = form.querySelector('[name="receiverCP"]')?.value;
        const receiverCountry = form.querySelector('[name="receiverCountry"]')?.value || 'FR';

        // Conditions minimales pour simuler
        if (!weight || !receiverCP) return;

        try {
            const data = {
                sender_iso: 'FR',
                sender_zip: senderCP || '75001',
                sender_city: 'PARIS',
                recipient_iso: receiverCountry,
                recipient_zip: receiverCP,
                recipient_city: 'VILLE',
                weight: parseFloat(weight)
            };

            const response = await fetch(config.apiSimulate, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) return;

            const result = await response.json();
            if (result.status === 'success' && result.offers) {
                // Trouver l'offre qui correspond au label (ex: "Chrono 10")
                const offer = result.offers.find(o => o.label.toLowerCase().includes(config.offerLabel.toLowerCase()));
                
                if (offer) {
                    currentCalculatedPrice = offer.price;
                    updateButton(currentCalculatedPrice);
                }
            }
        } catch (err) {
            console.error("Erreur simulation:", err);
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

        const watchFields = ['packageWeight', 'senderCP', 'receiverCP'];
        watchFields.forEach(name => {
            const field = form.querySelector(`[name="${name}"]`);
            if (field) {
                field.addEventListener('change', calculatePrice);
                field.addEventListener('blur', calculatePrice);
            }
        });

        // Premier calcul si déjà rempli (ex: session storage)
        setTimeout(calculatePrice, 500);
    });

})();
