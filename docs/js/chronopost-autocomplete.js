function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

const initAutocomplete = () => {
    console.log("Initialisation Autocomplete...");

    const CP_SELECTORS = [
        'input[name$="_cp"]', 'input[name$="CP"]', 'input[name="cp"]', 'input[name$="_zip"]', 'input[name$="zip"]', 'input[name="postal_code"]'
    ];

    function validateField(input) {
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
            if (errorSpan) {
                errorSpan.remove();
            }
        }
        return isValid;
    }

    window.validateForm = function(form) {
        let isFormValid = true;
        const inputs = form.querySelectorAll('input[required], select[required], input[pattern]');
        inputs.forEach(input => {
            if (!validateField(input)) {
                isFormValid = false;
            }
        });
        return isFormValid;
    };

    function setupCityAutocomplete(cpInput) {
        if (!cpInput) return;

        let cityInput = null;
        let countryInput = null;
        const name = cpInput.name.toLowerCase();

        // Support de _cp ou _zip
        if (name.endsWith('_cp') || name.endsWith('_zip')) {
            const suffix = name.endsWith('_cp') ? '_cp' : '_zip';
            const prefix = cpInput.name.substring(0, cpInput.name.length - suffix.length);
            cityInput = document.querySelector(`input[name="${prefix}_ville"]`) || document.querySelector(`input[name="${prefix}_city"]`);
            countryInput = document.querySelector(`select[name="${prefix}_pays"]`) || 
                          document.querySelector(`input[name="${prefix}_pays"]`) ||
                          document.querySelector(`select[name="${prefix}_iso"]`) ||
                          document.querySelector(`input[name="${prefix}_iso"]`);
        } else if (name.endsWith('cp') && name !== 'cp') {
            const prefix = cpInput.name.substring(0, cpInput.name.length - 2);
            cityInput = document.querySelector(`input[name="${prefix}City"]`) || document.querySelector(`input[name="${prefix}Ville"]`);
            countryInput = document.querySelector(`input[name="${prefix}Country"]`) || 
                          document.querySelector(`select[name="${prefix}Country"]`) ||
                          document.querySelector(`input[name="${prefix}ISO"]`);
        } else if (name === 'cp' || name === 'zip') {
            cityInput = document.querySelector('input[name="ville"]') || document.querySelector('input[name="city"]');
            countryInput = document.querySelector('input[name="pays"]') || 
                          document.querySelector('select[name="pays"]') ||
                          document.querySelector('input[name="iso"]');
        }

        if (!cityInput) return;

        const citiesListId = `city-list-${Math.random().toString(36).substr(2, 9)}`;
        let citiesList = document.createElement('datalist');
        citiesList.id = citiesListId;
        document.body.appendChild(citiesList);
        cityInput.setAttribute('list', citiesListId);

        const fetchCities = async function () {
            const zip = cpInput.value;
            if (zip.length < 3) return;
            
            // Si on a un pays et que ce n'est pas la France (FR), on ne fait rien
            if (countryInput && countryInput.value && countryInput.value.toUpperCase() !== 'FR') {
                console.log("Autocomplete ignoré (Pays != FR)");
                return;
            }

            try {
                console.log(`Recherche ville pour CP: ${zip}`);
                const response = await fetch(`https://geo.api.gouv.fr/communes?codePostal=${zip}&fields=nom&format=json`);
                const data = await response.json();

                citiesList.innerHTML = '';
                if (data.length === 1 && zip.length === 5) {
                    cityInput.value = data[0].nom;
                    console.log(`Ville trouvée: ${data[0].nom}`);
                } else if (data.length > 0) {
                    data.forEach(city => {
                        const option = document.createElement('option');
                        option.value = city.nom;
                        citiesList.appendChild(option);
                    });
                    console.log(`${data.length} villes trouvées`);
                }
            } catch (e) { console.error("Geo API Error", e); }
        };

        cpInput.addEventListener('input', debounce(fetchCities, 300));
    }

    function setupAddressAutocomplete(addrInput) {
        if (!addrInput) return;

        let zipInput = null;
        let countryInput = null;
        const name = addrInput.name.toLowerCase();

        if (name.endsWith('_adresse')) {
            const prefix = addrInput.name.split('_')[0];
            zipInput = document.querySelector(`input[name="${prefix}_cp"]`);
            countryInput = document.querySelector(`select[name="${prefix}_pays"]`);
        } else if (name.endsWith('address') || name === 'adresse') {
            const prefix = addrInput.name.replace(/address|adresse/i, '');
            zipInput = document.querySelector(`input[name="${prefix}CP"]`) || document.querySelector(`input[name="cp"]`);
            countryInput = document.querySelector(`input[name="${prefix}Country"]`) || document.querySelector(`input[name="pays"]`);
        }

        if (!zipInput) return;

        const streetListId = `street-list-${Math.random().toString(36).substr(2, 9)}`;
        let streetList = document.createElement('datalist');
        streetList.id = streetListId;
        document.body.appendChild(streetList);
        addrInput.setAttribute('list', streetListId);
        addrInput.setAttribute('autocomplete', 'off');

        const fetchAddresses = async function () {
            const query = addrInput.value;
            if (query.length < 4) return;
            if (countryInput && countryInput.value && countryInput.value.toUpperCase() !== 'FR') return;

            let apiUrl = `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(query)}&limit=6`;

            if (zipInput && zipInput.value.length === 5) {
                apiUrl += `&postcode=${zipInput.value}`;
            }

            try {
                const response = await fetch(apiUrl);
                const data = await response.json();

                streetList.innerHTML = '';

                if (data.features && data.features.length > 0) {
                    data.features.forEach(feature => {
                        const props = feature.properties;
                        const option = document.createElement('option');
                        option.value = props.name;
                        option.dataset.zip = props.postcode;
                        option.dataset.city = props.city;
                        option.label = `${props.postcode} ${props.city}`;
                        streetList.appendChild(option);
                    });
                }
            } catch (e) { console.error("Address API Error", e); }
        };

        addrInput.addEventListener('input', debounce(fetchAddresses, 300));

        addrInput.addEventListener('change', function () {
            const val = this.value;
            const options = streetList.childNodes;
            for (let i = 0; i < options.length; i++) {
                if (options[i].value === val) {
                    if (zipInput) zipInput.value = options[i].dataset.zip;

                    const nameBase = addrInput.name.replace(/address|adresse/i, '');
                    const cityField = document.querySelector(`input[name="${nameBase}City"]`) ||
                        document.querySelector(`input[name="${nameBase}Ville"]`) ||
                        document.querySelector('input[name="ville"]') ||
                        document.querySelector('input[name="city"]');
                    if (cityField) cityField.value = options[i].dataset.city;
                    break;
                }
            }
        });
    }

    function setupDynamicValidation() {
        if (!document.getElementById('dynamic-validation-style')) {
            const style = document.createElement('style');
            style.id = 'dynamic-validation-style';
            style.innerHTML = `
                .validation-error-msg {
                    color: #ff4444;
                    font-size: 0.75rem;
                    margin-top: 4px;
                    display: block;
                    font-weight: 500;
                }
                input.input-invalid, select.input-invalid {
                    border-color: #ff4444 !important;
                    box-shadow: 0 0 0 2px rgba(255, 68, 68, 0.1) !important;
                }
            `;
            document.head.appendChild(style);
        }

        const inputs = document.querySelectorAll('input[required], select[required], input[pattern], input[type="email"], input[type="tel"]');

        inputs.forEach(input => {
            input.addEventListener('input', () => {
                if (input.classList.contains('input-invalid')) {
                    validateField(input);
                }
            });

            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('change', () => validateField(input));
        });
    }

    // Lancement
    document.querySelectorAll(CP_SELECTORS.join(',')).forEach(setupCityAutocomplete);
    const ADDR_SELECTORS = ['input[name$="_adresse"]', 'input[name$="Address"]', 'input[name$="_address"]', 'input[name="adresse"]', 'input[name="address"]'];
    document.querySelectorAll(ADDR_SELECTORS.join(',')).forEach(setupAddressAutocomplete);
    setupDynamicValidation();
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAutocomplete);
} else {
    initAutocomplete();
}
