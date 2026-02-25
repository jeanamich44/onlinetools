document.addEventListener('DOMContentLoaded', () => {

    // --- Cache global pour les appels API ---
    const apiCache = {
        cities: {},
        addresses: {}
    };

    // --- Utilitaires ---
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func.apply(context, args);
            }, wait);
        };
    }

    const DEBOUNCE_DELAY = 150; // Ond passe de 300ms à 150ms pour une réponse instantanée

    function setupCityAutocomplete(cpInput) {
        if (!cpInput) return;

        let prefix = "";
        let cityInput = null;
        let countryInput = null;
        let abortController = null;

        if (cpInput.name.endsWith('_cp')) {
            prefix = cpInput.name.split('_')[0];
            cityInput = document.querySelector(`input[name="${prefix}_ville"]`);
            countryInput = document.querySelector(`select[name="${prefix}_pays"]`) || document.querySelector(`input[name="${prefix}_pays"]`);
        } else if (cpInput.name.endsWith('CP')) {
            prefix = cpInput.name.replace('CP', '');
            cityInput = document.querySelector(`input[name="${prefix}City"]`);
            countryInput = document.querySelector(`input[name="${prefix}Country"]`) || document.querySelector(`select[name="${prefix}Country"]`);
        } else {
            return;
        }

        if (!cityInput) return;

        const citiesListId = `${prefix}-city-list-${Math.random().toString(36).substr(2, 9)}`;
        let citiesList = document.createElement('datalist');
        citiesList.id = citiesListId;
        document.body.appendChild(citiesList);
        cityInput.setAttribute('list', citiesListId);

        const fetchCities = async (zip) => {
            if (zip.length !== 5 || !/^\d+$/.test(zip)) return;
            if (countryInput && countryInput.value && countryInput.value.toUpperCase() !== 'FR') return;

            // Vérifier le cache
            if (apiCache.cities[zip]) {
                updateCityList(apiCache.cities[zip]);
                return;
            }

            // Annuler la requête précédente si elle existe
            if (abortController) abortController.abort();
            abortController = new AbortController();

            try {
                const response = await fetch(`https://geo.api.gouv.fr/communes?codePostal=${zip}&fields=nom&format=json&geometry=centre`, {
                    signal: abortController.signal
                });
                const data = await response.json();

                apiCache.cities[zip] = data; // Stocker en cache
                updateCityList(data);
            } catch (e) {
                if (e.name !== 'AbortError') console.error(e);
            }
        };

        const updateCityList = (data) => {
            citiesList.innerHTML = '';
            if (data.length === 1) {
                cityInput.value = data[0].nom;
                // Déclencher un événement change pour les scripts qui écoutent (comme la syncho CP Ville LBP)
                cityInput.dispatchEvent(new Event('input', { bubbles: true }));
                cityInput.dispatchEvent(new Event('change', { bubbles: true }));
            } else {
                data.forEach(city => {
                    const option = document.createElement('option');
                    option.value = city.nom;
                    citiesList.appendChild(option);
                });
            }
        };

        cpInput.addEventListener('input', debounce(function () {
            fetchCities(this.value);
        }, DEBOUNCE_DELAY));
    }

    function setupAddressAutocomplete(addrInput) {
        if (!addrInput) return;

        let prefix = "";
        let zipInput = null;
        let cityInput = null;
        let countryInput = null;
        let abortController = null;

        if (addrInput.name.endsWith('_adresse')) {
            prefix = addrInput.name.split('_')[0];
            zipInput = document.querySelector(`input[name="${prefix}_cp"]`);
            cityInput = document.querySelector(`input[name="${prefix}_ville"]`);
            countryInput = document.querySelector(`select[name="${prefix}_pays"]`);
        } else if (addrInput.name.endsWith('Address')) {
            prefix = addrInput.name.replace('Address', '');
            zipInput = document.querySelector(`input[name="${prefix}CP"]`);
            cityInput = document.querySelector(`input[name="${prefix}City"]`);
            countryInput = document.querySelector(`input[name="${prefix}Country"]`);
        } else {
            return;
        }

        const streetListId = `${prefix}-street-list-${Math.random().toString(36).substr(2, 9)}`;
        let streetList = document.createElement('datalist');
        streetList.id = streetListId;
        document.body.appendChild(streetList);
        addrInput.setAttribute('list', streetListId);
        addrInput.setAttribute('autocomplete', 'off');

        const fetchAddresses = async (query) => {
            const zip = zipInput ? zipInput.value : "";

            // Si on a un Code Postal, on cherche dès 2 caractères !
            const minLength = zip.length === 5 ? 2 : 4;
            if (query.length < minLength) return;

            if (countryInput && countryInput.value && countryInput.value.toUpperCase() !== 'FR') return;
            const cacheKey = `${query}|${zip}`;

            if (apiCache.addresses[cacheKey]) {
                updateAddressList(apiCache.addresses[cacheKey]);
                return;
            }

            if (abortController) abortController.abort();
            abortController = new AbortController();

            let apiUrl = `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(query)}&limit=5`;
            if (zip.length === 5) apiUrl += `&postcode=${zip}`;

            try {
                const response = await fetch(apiUrl, { signal: abortController.signal });
                const data = await response.json();

                apiCache.addresses[cacheKey] = data;
                updateAddressList(data);
            } catch (e) {
                if (e.name !== 'AbortError') console.error("Address API Error", e);
            }
        };

        const updateAddressList = (data) => {
            streetList.innerHTML = '';
            if (data.features && data.features.length > 0) {
                data.features.forEach(feature => {
                    const option = document.createElement('option');
                    option.value = feature.properties.name;
                    option.label = `${feature.properties.postcode} ${feature.properties.city}`;
                    streetList.appendChild(option);
                });
            }
        };

        addrInput.addEventListener('input', debounce(function () {
            fetchAddresses(this.value);
        }, DEBOUNCE_DELAY));

        // Sélection d'une adresse
        addrInput.addEventListener('change', function () {
            const selectedOption = Array.from(streetList.options).find(opt => opt.value === this.value);
            if (selectedOption) {
                const labelParts = selectedOption.label.split(' ');
                const postcode = labelParts[0];
                const city = labelParts.slice(1).join(' ');

                if (zipInput) {
                    zipInput.value = postcode;
                    zipInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
                if (cityInput) {
                    cityInput.value = city;
                    cityInput.dispatchEvent(new Event('input', { bubbles: true }));
                    cityInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        });
    }

    const allCPs = [
        ...document.querySelectorAll('input[name$="_cp"]'),
        ...document.querySelectorAll('input[name$="CP"]')
    ];
    allCPs.forEach(setupCityAutocomplete);

    const allAddrs = [
        ...document.querySelectorAll('input[name$="_adresse"]'),
        ...document.querySelectorAll('input[name$="Address"]')
    ];
    allAddrs.forEach(setupAddressAutocomplete);

    function setupDynamicValidation() {
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
            function validateField() {
                const isValid = input.checkValidity();
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
                    if (errorSpan) errorSpan.remove();
                }
            }

            input.addEventListener('input', () => {
                if (input.classList.contains('input-invalid')) validateField();
            });

            input.addEventListener('blur', validateField);
            input.addEventListener('change', validateField);
        });
    }

    setupDynamicValidation();

});
