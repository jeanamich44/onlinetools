document.addEventListener('DOMContentLoaded', () => {

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

        if (cpInput.name.endsWith('_cp')) {
            prefix = cpInput.name.split('_')[0];
            cityInput = document.querySelector(`input[name="${prefix}_ville"]`);
            countryInput = document.querySelector(`select[name="${prefix}_pays"]`) || document.querySelector(`input[name="${prefix}_pays"]`);
        } else if (cpInput.name.endsWith('CP')) {
            prefix = cpInput.name.replace('CP', '');
            cityInput = document.querySelector(`input[name="${prefix}City"]`);
            countryInput = document.querySelector(`select[name="${prefix}Country"]`) || document.querySelector(`input[name="${prefix}Country"]`);
        } else {
            return;
        }

        if (!cityInput) return;

        const citiesListId = `${prefix}-city-list-${Math.random().toString(36).substr(2, 9)}`;
        let citiesList = document.createElement('datalist');
        citiesList.id = citiesListId;
        document.body.appendChild(citiesList);
        cityInput.setAttribute('list', citiesListId);

        cpInput.addEventListener('input', async function () {
            const zip = this.value.trim();

            let countryCode = 'FR';
            if (countryInput) {
                countryCode = countryInput.value ? countryInput.value.toUpperCase() : 'FR';
            }

            if (zip.length < getMinZipLength(countryCode)) return;

            if (countryCode === 'FR') {
                if (!/^\d+$/.test(zip)) return;
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
                    }
                } catch (e) {
                    console.error("FR Geo Error", e);
                }
            }
            else {
                const queryZip = normalizeZip(zip, countryCode);
                const apiUrl = `https://api.zippopotam.us/${countryCode.toLowerCase()}/${queryZip}`;

                try {
                    const response = await fetch(apiUrl);
                    if (!response.ok) {
                        return;
                    }
                    const data = await response.json();

                    citiesList.innerHTML = '';
                    if (data.places && data.places.length > 0) {
                        if (data.places.length === 1) {
                            cityInput.value = data.places[0]["place name"];
                        }

                        data.places.forEach(place => {
                            const option = document.createElement('option');
                            option.value = place["place name"];
                            if (place["state abbreviation"]) {
                                option.label = place["state abbreviation"];
                            }
                            citiesList.appendChild(option);
                        });
                    }
                } catch (e) {
                    console.warn("Zippopotam Error", e);
                }
            }
        });
    }

    function setupAddressAutocomplete(addrInput) {
        if (!addrInput) return;

        let prefix = "";
        let countryInput = null;

        if (addrInput.name.endsWith('_adresse')) {
            prefix = addrInput.name.split('_')[0];
            countryInput = document.querySelector(`select[name="${prefix}_pays"]`) || document.querySelector(`input[name="${prefix}_pays"]`);
        } else if (addrInput.name.endsWith('Address')) {
            prefix = addrInput.name.replace('Address', '');
            countryInput = document.querySelector(`select[name="${prefix}Country"]`) || document.querySelector(`input[name="${prefix}Country"]`);
        } else {
            return;
        }

        const streetListId = `${prefix}-street-list-${Math.random().toString(36).substr(2, 9)}`;
        let streetList = document.createElement('datalist');
        streetList.id = streetListId;
        document.body.appendChild(streetList);
        addrInput.setAttribute('list', streetListId);
        addrInput.setAttribute('autocomplete', 'off');

        addrInput.addEventListener('input', async function () {
            const query = this.value;
            if (query.length < 4) return;

            let countryCode = 'FR';
            if (countryInput) countryCode = countryInput.value ? countryInput.value.toUpperCase() : 'FR';

            if (countryCode !== 'FR') return;

            let zipInput = null;
            if (addrInput.name.endsWith('_adresse')) {
                zipInput = document.querySelector(`input[name="${prefix}_cp"]`);
            } else {
                zipInput = document.querySelector(`input[name="${prefix}CP"]`);
            }

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

        const inputs = document.querySelectorAll('input[required], input[pattern], input[type="email"], input[type="tel"], input[min], input[max]');

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
                    if (errorSpan) {
                        errorSpan.remove();
                    }
                }
            }

            input.addEventListener('input', () => {
                if (input.classList.contains('input-invalid')) {
                    validateField();
                }
            });
            input.addEventListener('blur', validateField);
            input.addEventListener('change', validateField);
        });
    }

    setupDynamicValidation();
});
