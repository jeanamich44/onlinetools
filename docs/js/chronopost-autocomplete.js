/**
 * Chronopost Address Autocomplete
 * Uses geo.api.gouv.fr (Cities) and api-adresse.data.gouv.fr (Streets)
 * Supports: 
 *  - Old format: name="{prefix}_cp" / "{prefix}_ville" / "{prefix}_adresse" (e.g. exp_cp)
 *  - New format: name="{prefix}CP" / "{prefix}City" / "{prefix}Address" (e.g. senderCP)
 */

document.addEventListener('DOMContentLoaded', () => {

    function setupCityAutocomplete(cpInput) {
        if (!cpInput) return;

        let prefix = "";
        let cityInput = null;
        let countryInput = null;

        // Detect Format
        if (cpInput.name.endsWith('_cp')) {
            // Old format
            prefix = cpInput.name.split('_')[0];
            cityInput = document.querySelector(`input[name="${prefix}_ville"]`);
            countryInput = document.querySelector(`select[name="${prefix}_pays"]`) || document.querySelector(`input[name="${prefix}_pays"]`);
        } else if (cpInput.name.endsWith('CP')) {
            // New format (senderCP, receiverCP)
            prefix = cpInput.name.replace('CP', '');
            cityInput = document.querySelector(`input[name="${prefix}City"]`);
            countryInput = document.querySelector(`input[name="${prefix}Country"]`) || document.querySelector(`select[name="${prefix}Country"]`);
        } else {
            return;
        }

        if (!cityInput) return;

        // Create datalist for cities
        const citiesListId = `${prefix}-city-list-${Math.random().toString(36).substr(2, 9)}`;
        let citiesList = document.createElement('datalist');
        citiesList.id = citiesListId;
        document.body.appendChild(citiesList);
        cityInput.setAttribute('list', citiesListId);

        // ZIP Input Listener
        cpInput.addEventListener('input', async function () {
            const zip = this.value;
            if (zip.length !== 5 || !/^\d+$/.test(zip)) return;
            // Check country if exists (allow if FR or empty/hidden FR)
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
                    // Hint user
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

        // Create datalist for streets
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

    // Initialize for all potential CP inputs
    const allCPs = [
        ...document.querySelectorAll('input[name$="_cp"]'),
        ...document.querySelectorAll('input[name$="CP"]')
    ];
    allCPs.forEach(setupCityAutocomplete);

    // Initialize for all potential Address inputs
    const allAddrs = [
        ...document.querySelectorAll('input[name$="_adresse"]'),
        ...document.querySelectorAll('input[name$="Address"]')
    ];
    allAddrs.forEach(setupAddressAutocomplete);

});
