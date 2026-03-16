document.addEventListener('DOMContentLoaded', () => {

    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    function getMinZipLength(country) {
        switch (country) {
            case 'US': return 5;
            case 'DE': return 5;
            case 'FR': return 5;
            case 'ES': return 5;
            case 'IT': return 5;
            case 'CA': return 3;
            case 'GB': return 2;
            default: return 2;
        }
    }

    function normalizeZip(zip, country) {
        let z = zip.trim();
        if (country === 'CA') {
            return z.substring(0, 3);
        }
        if (country === 'GB') {
            return z.split(' ')[0];
        }
        return z;
    }

    function setupCityAutocomplete(cpInput) {
        if (!cpInput) return;

        let prefix = "";
        let cityInput = null;
        let countryInput = null;
        const name = cpInput.name;
        const nameLower = name.toLowerCase();

        if (name.includes('_')) {
            prefix = name.substring(0, name.lastIndexOf('_'));
        } else if (nameLower.startsWith('sender')) {
            prefix = name.substring(0, 6);
        } else if (nameLower.startsWith('receiver')) {
            prefix = name.substring(0, 8);
        } else if (nameLower.startsWith('agence')) {
            prefix = name.substring(0, 6);
        }

        if (prefix) {
            cityInput = document.querySelector(`input[name="${prefix}_ville"]`) || 
                        document.querySelector(`input[name="${prefix}_city"]`) ||
                        document.querySelector(`input[name="${prefix}Ville"]`) ||
                        document.querySelector(`input[name="${prefix}City"]`);
            
            countryInput = document.querySelector(`select[name="${prefix}_iso"]`) || 
                          document.querySelector(`input[name="${prefix}_iso"]`) ||
                          document.querySelector(`select[name="${prefix}_pays"]`) ||
                          document.querySelector(`input[name="${prefix}_pays"]`) ||
                          document.querySelector(`select[name="${prefix}Country"]`) ||
                          document.querySelector(`input[name="${prefix}Country"]`) ||
                          document.querySelector(`input[id="recipientCountryHidden"]`);
        } else {
            cityInput = document.querySelector('input[name="ville"]') || document.querySelector('input[name="city"]');
            countryInput = document.querySelector('select[name="iso"]') || document.querySelector('input[name="iso"]') || 
                          document.querySelector('select[name="pays"]') || document.querySelector('input[name="pays"]');
        }

        if (!cityInput) return;

        const citiesListId = `${prefix}-city-list-${Math.random().toString(36).substr(2, 9)}`;
        let citiesList = document.createElement('datalist');
        citiesList.id = citiesListId;
        document.body.appendChild(citiesList);
        cityInput.setAttribute('list', citiesListId);

        const fetchCities = async function () {
            const zip = cpInput.value.trim();

            let countryCode = 'FR';
            if (countryInput) {
                countryCode = countryInput.value ? countryInput.value.toUpperCase() : 'FR';
            }

            if (zip.length < getMinZipLength(countryCode)) return;

            if (['FR', 'GP', 'GF', 'MQ', 'RE', 'YT', 'BL', 'MF'].includes(countryCode)) {
                try {
                    const response = await fetch(`https://geo.api.gouv.fr/communes?codePostal=${zip}&fields=nom&format=json&geometry=centre`);
                    const data = await response.json();

                    citiesList.innerHTML = '';
                    if (data.length === 1 && zip.length === 5) {
                        cityInput.value = data[0].nom;
                    } else if (data.length > 0) {
                        data.forEach(city => {
                            const option = document.createElement('option');
                            option.value = city.nom;
                            citiesList.appendChild(option);
                        });
                    }
                } catch (e) {}
            }
            else {
                const queryZip = normalizeZip(zip, countryCode);
                const apiUrl = `https://api.zippopotam.us/${countryCode.toLowerCase()}/${queryZip}`;

                try {
                    const response = await fetch(apiUrl);
                    if (!response.ok) return;
                    const data = await response.json();

                    citiesList.innerHTML = '';
                    if (data.places && data.places.length > 0) {
                        if (data.places.length === 1) {
                            let cityName = data.places[0]["place name"];
                            if (cityName.includes(' (')) cityName = cityName.split(' (')[0];
                            const parts = cityName.split(' ');
                            if (parts.length > 1 && ['Downtown', 'North', 'South', 'East', 'West', 'Central'].includes(parts[0])) {
                                cityName = parts.slice(1).join(' ');
                            }
                            cityInput.value = cityName;
                        }

                        data.places.forEach(place => {
                            let cityName = place["place name"];
                            if (cityName.includes(' (')) cityName = cityName.split(' (')[0];
                            const parts = cityName.split(' ');
                            if (parts.length > 1 && ['Downtown', 'North', 'South', 'East', 'West', 'Central'].includes(parts[0])) {
                                cityName = parts.slice(1).join(' ');
                            }
                            const option = document.createElement('option');
                            option.value = cityName;
                            if (place["state abbreviation"]) {
                                option.label = place["state abbreviation"];
                            }
                            citiesList.appendChild(option);
                        });
                    }
                } catch (e) {}
            }
        };

        cpInput.addEventListener('input', debounce(fetchCities, 300));
    }

    function setupAddressAutocomplete(addrInput) {
        if (!addrInput) return;

        let prefix = "";
        let countryInput = null;
        let zipInput = null;
        const name = addrInput.name;
        const nameLower = name.toLowerCase();

        if (name.includes('_')) {
            prefix = name.substring(0, name.lastIndexOf('_'));
        } else if (nameLower.startsWith('sender')) {
            prefix = name.substring(0, 6);
        } else if (nameLower.startsWith('receiver')) {
            prefix = name.substring(0, 8);
        } else if (nameLower.startsWith('agence')) {
            prefix = name.substring(0, 6);
        }

        if (prefix) {
            zipInput = document.querySelector(`input[name="${prefix}_cp"]`) || 
                      document.querySelector(`input[name="${prefix}_zip"]`) ||
                      document.querySelector(`input[name="${prefix}CP"]`) ||
                      document.querySelector(`input[name="${prefix}Zip"]`);
            
            countryInput = document.querySelector(`select[name="${prefix}_iso"]`) || 
                          document.querySelector(`input[name="${prefix}_iso"]`) ||
                          document.querySelector(`select[name="${prefix}Country"]`) ||
                          document.querySelector(`input[name="${prefix}Country"]`);
        }

        const streetListId = `${prefix}-street-list-${Math.random().toString(36).substr(2, 9)}`;
        let streetList = document.createElement('datalist');
        streetList.id = streetListId;
        document.body.appendChild(streetList);
        addrInput.setAttribute('list', streetListId);
        addrInput.setAttribute('autocomplete', 'off');

        const fetchAddresses = async function () {
            const query = addrInput.value;
            if (query.length < 4) return;

            let countryCode = 'FR';
            if (countryInput) countryCode = countryInput.value ? countryInput.value.toUpperCase() : 'FR';

            if (countryCode !== 'FR') return;

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
                        const props = feature.properties;
                        const option = document.createElement('option');
                        option.value = props.name;
                        option.dataset.zip = props.postcode;
                        option.dataset.city = props.city;
                        option.label = `${props.postcode} ${props.city}`;
                        streetList.appendChild(option);
                    });
                }
            } catch (e) {}
        };

        addrInput.addEventListener('input', debounce(fetchAddresses, 300));
        
        addrInput.addEventListener('change', function () {
            const val = this.value;
            const options = streetList.childNodes;
            for (let i = 0; i < options.length; i++) {
                if (options[i].value === val) {
                    if (zipInput) zipInput.value = options[i].dataset.zip;
                    
                    let cityField = null;
                    if (prefix) {
                        cityField = document.querySelector(`input[name="${prefix}_city"]`) || 
                                    document.querySelector(`input[name="${prefix}_ville"]`) ||
                                    document.querySelector(`input[name="${prefix}City"]`) ||
                                    document.querySelector(`input[name="${prefix}Ville"]`);
                    } else {
                        cityField = document.querySelector(`input[name="city"]`) || document.querySelector(`input[name="ville"]`);
                    }

                    if (cityField) cityField.value = options[i].dataset.city;
                    break;
                }
            }
        });
    }

    const CP_SELECTORS = [
        'input[name$="_cp"]', 'input[name$="CP"]', 'input[name="cp"]', 'input[name$="_zip"]', 'input[name$="zip"]', 'input[name="postal_code"]'
    ];
    document.querySelectorAll(CP_SELECTORS.join(',')).forEach(setupCityAutocomplete);

    const ADDR_SELECTORS = [
        'input[name$="_adresse"]', 'input[name$="Address"]', 'input[name="adresse"]', 'input[name="address"]'
    ];
    document.querySelectorAll(ADDR_SELECTORS.join(',')).forEach(setupAddressAutocomplete);

    function setupDynamicValidation() {
        if (!document.getElementById('dynamic-validation-style')) {
            const style = document.createElement('style');
            style.id = 'dynamic-validation-style';
            style.innerHTML = `
                .validation-error-msg { color: #ff4444; font-size: 0.8rem; margin-top: 4px; display: block; font-weight: 500; }
                input.input-invalid, select.input-invalid { border-color: #ff4444 !important; box-shadow: 0 0 0 2px rgba(255, 68, 68, 0.1) !important; }
            `;
            document.head.appendChild(style);
        }

        const selector = 'input[required], select[required], input[pattern], input[type="email"], input[type="tel"], input[min], input[max]';
        const inputs = document.querySelectorAll(selector);

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
