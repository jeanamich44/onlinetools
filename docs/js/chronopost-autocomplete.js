/**
 * Autocomplétion Adresse Chronopost
 * Utilise geo.api.gouv.fr (Villes) et api-adresse.data.gouv.fr (Rues)
 * Supporte : 
 *  - Ancien format : name="{prefix}_cp" / "{prefix}_ville" / "{prefix}_adresse" (ex: exp_cp)
 *  - Nouveau format : name="{prefix}CP" / "{prefix}City" / "{prefix}Address" (ex: senderCP)
 */

document.addEventListener('DOMContentLoaded', () => {

    function setupCityAutocomplete(cpInput) {
        if (!cpInput) return;

        let prefix = "";
        let cityInput = null;
        let countryInput = null;

        // Détection du format
        if (cpInput.name.endsWith('_cp')) {
            // Ancien format
            prefix = cpInput.name.split('_')[0];
            cityInput = document.querySelector(`input[name="${prefix}_ville"]`);
            countryInput = document.querySelector(`select[name="${prefix}_pays"]`) || document.querySelector(`input[name="${prefix}_pays"]`);
        } else if (cpInput.name.endsWith('CP')) {
            // Nouveau format (senderCP, receiverCP)
            prefix = cpInput.name.replace('CP', '');
            cityInput = document.querySelector(`input[name="${prefix}City"]`);
            countryInput = document.querySelector(`input[name="${prefix}Country"]`) || document.querySelector(`select[name="${prefix}Country"]`);
        } else {
            return;
        }

        if (!cityInput) return;

        // Création de la datalist pour les villes
        const citiesListId = `${prefix}-city-list-${Math.random().toString(36).substr(2, 9)}`;
        let citiesList = document.createElement('datalist');
        citiesList.id = citiesListId;
        document.body.appendChild(citiesList);
        cityInput.setAttribute('list', citiesListId);

        // Écouteur Input Code Postal
        cpInput.addEventListener('input', async function () {
            const zip = this.value;
            if (zip.length !== 5 || !/^\d+$/.test(zip)) return;
            // Vérifie le pays s'il existe (autorise si FR ou vide/caché FR)
            if (countryInput && countryInput.value && countryInput.value.toUpperCase() !== 'FR') return;

            try {
                const response = await fetch(`https://geo.api.gouv.fr/communes?codePostal=${zip}&fields=nom&format=json&geometry=centre`);
                const data = await response.json();

                citiesList.innerHTML = '';
                if (data.length === 1) {
                    cityInput.value = data[0].nom;
                } else {
                    data.forEach(city => {
                        const option = document.createElement('option');
                        option.value = city.nom;
                        citiesList.appendChild(option);
                    });
                    // Indice utilisateur
                    if (!cityInput.value) {
                        // Optional: cityInput.placeholder = "Sélectionnez...";
                    }
                }
            } catch (e) { console.error(e); }
        });
    }

    function setupAddressAutocomplete(addrInput) {
        if (!addrInput) return;

        let prefix = "";
        let zipInput = null;
        let countryInput = null;

        if (addrInput.name.endsWith('_adresse')) {
            prefix = addrInput.name.split('_')[0];
            zipInput = document.querySelector(`input[name="${prefix}_cp"]`);
            countryInput = document.querySelector(`select[name="${prefix}_pays"]`);
        } else if (addrInput.name.endsWith('Address')) {
            prefix = addrInput.name.replace('Address', '');
            zipInput = document.querySelector(`input[name="${prefix}CP"]`);
            countryInput = document.querySelector(`input[name="${prefix}Country"]`);
        } else {
            return;
        }

        // Création de la datalist pour les rues
        const streetListId = `${prefix}-street-list-${Math.random().toString(36).substr(2, 9)}`;
        let streetList = document.createElement('datalist');
        streetList.id = streetListId;
        document.body.appendChild(streetList);
        addrInput.setAttribute('list', streetListId);
        addrInput.setAttribute('autocomplete', 'off');

        addrInput.addEventListener('input', async function () {
            const query = this.value;
            if (query.length < 4) return;
            if (countryInput && countryInput.value && countryInput.value.toUpperCase() !== 'FR') return;

            let apiUrl = `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(query)}&limit=5`;

            if (zipInput && zipInput.value.length === 5) {
                apiUrl += `&postcode=${zipInput.value}`;
            }

            try {
                const response = await fetch(apiUrl);
                const data = await response.json();

                streetList.innerHTML = '';

                if (data.features && data.features.length > 0) {
                    data.features.forEach(feature => {
                        const validAddress = feature.properties.name;
                        const contextMap = feature.properties;
                        const option = document.createElement('option');
                        option.value = validAddress;
                        option.label = `${contextMap.postcode} ${contextMap.city}`;
                        streetList.appendChild(option);
                    });
                }
            } catch (e) { console.error("Address API Error", e); }
        });
    }

    // Initialisation pour tous les inputs CP potentiels
    const allCPs = [
        ...document.querySelectorAll('input[name$="_cp"]'),
        ...document.querySelectorAll('input[name$="CP"]')
    ];
    allCPs.forEach(setupCityAutocomplete);

    // Initialisation pour tous les inputs Adresse potentiels
    const allAddrs = [
        ...document.querySelectorAll('input[name$="_adresse"]'),
        ...document.querySelectorAll('input[name$="Address"]')
    ];
    allAddrs.forEach(setupAddressAutocomplete);

    // --- Dynamic Validation Logic ---
    function setupDynamicValidation() {
        // Create error message style if not exists
        if (!document.getElementById('dynamic-validation-style')) {
            const style = document.createElement('style');
            style.id = 'dynamic-validation-style';
            style.innerHTML = `
                .validation-error-msg {
                    color: #ff4444;
                    font-size: 0.8rem;
                    margin-top: 4px;
                    display: block;
                }
                input.input-invalid {
                    border-color: #ff4444 !important;
                }
            `;
            document.head.appendChild(style);
        }

        const inputs = document.querySelectorAll('input[required], input[pattern], input[type="email"], input[type="tel"]');

        inputs.forEach(input => {
            // Helper to show/hide error
            function validateField() {
                // If it's valid check
                const isValid = input.checkValidity();

                // Find existing error msg
                let errorSpan = input.parentNode.querySelector('.validation-error-msg');

                if (!isValid) {
                    input.classList.add('input-invalid');
                    if (!errorSpan) {
                        errorSpan = document.createElement('span');
                        errorSpan.className = 'validation-error-msg';
                        input.parentNode.appendChild(errorSpan);
                    }
                    errorSpan.textContent = input.validationMessage;
                } else {
                    input.classList.remove('input-invalid');
                    if (errorSpan) {
                        errorSpan.remove();
                    }
                }
            }

            // Real-time on input (for length/pattern)
            input.addEventListener('input', () => {
                // Only show error if it was already marked invalid or if user is typing
                // actually standard UX is show success immediately, show error on blur OR if typing and it becomes valid
                // User asked "dynamic and automatic". 
                // Let's validate on input IF the field is dirty or invalid.
                if (input.classList.contains('input-invalid')) {
                    validateField();
                }
            });

            // On Blur (when leaving the field)
            input.addEventListener('blur', validateField);

            // On Change
            input.addEventListener('change', validateField);
        });
    }

    setupDynamicValidation();

});
