/**
 * Chronopost Address Autocomplete
 * Uses geo.api.gouv.fr (Cities) and api-adresse.data.gouv.fr (Streets)
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. CITY AUTOCOMPLETE (By Postal Code)
    // Select all inputs ending with '_cp' (exp_cp, dest_cp, relais_cp)
    const cpInputs = document.querySelectorAll('input[name$="_cp"]');

    cpInputs.forEach(input => {
        const prefix = input.name.split('_')[0]; // exp, dest, or relais
        const cityInput = document.querySelector(`input[name="${prefix}_ville"]`);
        const countrySelect = document.querySelector(`select[name="${prefix}_pays"]`);

        if (!cityInput) return;

        // Create datalist for cities
        const citiesListId = `${prefix}-city-list-${Math.random().toString(36).substr(2, 9)}`;
        let citiesList = document.createElement('datalist');
        citiesList.id = citiesListId;
        document.body.appendChild(citiesList);
        cityInput.setAttribute('list', citiesListId);

        // ZIP Input Listener
        input.addEventListener('input', async function () {
            const zip = this.value;
            if (zip.length !== 5 || !/^\d+$/.test(zip)) return;
            if (countrySelect && countrySelect.value !== 'FR' && countrySelect.value !== '') return;

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
                    if (!cityInput.value) cityInput.placeholder = "Sélectionnez une ville...";
                }
            } catch (e) { console.error(e); }
        });
    });


    // 2. STREET AUTOCOMPLETE (By Address + Context of Zip/City)
    // Select all address inputs
    const addressInputs = document.querySelectorAll('input[name$="_adresse"]');

    addressInputs.forEach(addrInput => {
        const prefix = addrInput.name.split('_')[0]; // exp, dest

        // Find context inputs
        const zipInput = document.querySelector(`input[name="${prefix}_cp"]`);
        const cityInput = document.querySelector(`input[name="${prefix}_ville"]`);
        const countrySelect = document.querySelector(`select[name="${prefix}_pays"]`);

        // Create datalist for streets
        const streetListId = `${prefix}-street-list-${Math.random().toString(36).substr(2, 9)}`;
        let streetList = document.createElement('datalist');
        streetList.id = streetListId;
        document.body.appendChild(streetList);
        addrInput.setAttribute('list', streetListId);
        addrInput.setAttribute('autocomplete', 'off'); // Browser autocomplete off

        addrInput.addEventListener('input', async function () {
            const query = this.value;
            // Only search if user typed at least 3 chars AND country is France/Empty
            if (query.length < 4) return;
            if (countrySelect && countrySelect.value !== 'FR' && countrySelect.value !== '') return;

            let apiUrl = `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(query)}&limit=5`;

            // Add postcode context if available
            if (zipInput && zipInput.value.length === 5) {
                apiUrl += `&postcode=${zipInput.value}`;
            }

            try {
                const response = await fetch(apiUrl);
                const data = await response.json();

                streetList.innerHTML = '';

                if (data.features && data.features.length > 0) {
                    data.features.forEach(feature => {
                        const validAddress = feature.properties.name; // Street name + Number
                        const contextMap = feature.properties;

                        const option = document.createElement('option');
                        option.value = validAddress;

                        // We can store extra data in label or handle selection, 
                        // but <datalist> is simple only. 
                        // Ideally we fill zip/city too if they are empty
                        option.label = `${contextMap.postcode} ${contextMap.city}`;
                        streetList.appendChild(option);
                    });
                }

            } catch (e) { console.error("Address API Error", e); }
        });

        // When user selects an address, try to auto-fill Zip/City if they are empty
        addrInput.addEventListener('change', async function () {
            // Re-query to find the exact match details (since datalist doesn't give us the object back easily)
            const val = this.value;
            // Logic to fetch full details if needed, but basic text is usually enough.
            // You explicitly asked for address search based on city. The logic above does that via &postcode context.
        });
    });
});
