let map;
let markersLayer;
let orangeIcon;

const RElAY_API_BASE = "https://transporteur.up.railway.app/relay/search";

// ==============================================================================

function initRelayMap(lat = 46.603354, lon = 1.888334, zoom = 5) {
    const mapDiv = document.getElementById('relayMap');
    if (!mapDiv || map) return;

    map = L.map('relayMap').setView([lat, lon], zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    markersLayer = L.layerGroup().addTo(map);

    orangeIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
    
    const zipInput = document.getElementById('mapZipInput');
    if (zipInput && zipInput.value.length >= 4) {
        searchRelays();
    }
}

// ==============================================================================

async function searchRelays() {
    const zipInput = document.getElementById('mapZipInput');
    const zip = zipInput?.value;
    const msgDiv = document.getElementById('mapSearchMsg');
    const listDiv = document.getElementById('relayList');
    const countryField = document.getElementById('destinationCountry');
    const country = countryField ? countryField.value : 'FR';

    if (!zip || zip.length < 4) {
        if (msgDiv) msgDiv.innerHTML = "<span style='color:#ff4444;'>Veuillez entrer un code postal.</span>";
        return;
    }

    if (msgDiv) msgDiv.innerHTML = "<span style='color:#0099ff;'>Recherche...</span>";
    if (listDiv) listDiv.innerHTML = "<div style='text-align:center; padding:20px;'><div class='spinner'></div></div>";

    try {
        let lat = 0, lon = 0;
        try {
            const geoResp = await fetch(`https://nominatim.openstreetmap.org/search?format=json&postalcode=${zip}&country=${country}&limit=1`);
            const geoData = await geoResp.json();
            if (geoData && geoData.length > 0) {
                lat = parseFloat(geoData[0].lat);
                lon = parseFloat(geoData[0].lon);
                map.setView([lat, lon], 13);
            }
        } catch (e) { }

        const url = `${RElAY_API_BASE}?zip=${zip}&type=chronopost&lat=${lat}&lon=${lon}&country=${country}`;
        const resp = await fetch(url);
        const data = await resp.json();

        markersLayer.clearLayers();
        if (listDiv) listDiv.innerHTML = "";

        if (data.status === 'success' && data.relays && data.relays.length > 0) {
            if (msgDiv) msgDiv.innerHTML = `<span style='color:#28a745;'>✅ ${data.relays.length} points trouvés.</span>`;
            
            data.relays.forEach(relay => {
                const marker = L.marker([relay.lat, relay.lng], { icon: orangeIcon });
                const popupContent = `
                    <div style="color:#000; min-width:150px;">
                        <b style="color:#0099ff;">${relay.name}</b><br>
                        ${relay.address}<br>
                        ${relay.zip} ${relay.city}<br>
                        <button onclick="selectChronopostRelay('${relay.id}', '${relay.name}', '${relay.address}', '${relay.zip}', '${relay.city}')" 
                                style="background:#238636; color:#fff; border:none; padding:8px; border-radius:4px; cursor:pointer; margin-top:8px; width:100%; font-weight:bold;">
                            Sélectionner
                        </button>
                    </div>
                `;
                marker.bindPopup(popupContent);
                markersLayer.addLayer(marker);

                if (listDiv) {
                    const card = document.createElement('div');
                    card.className = 'relay-card';
                    card.innerHTML = `
                        <div class="relay-card-title">${relay.name}</div>
                        <div class="relay-card-address">${relay.address}<br>${relay.zip} ${relay.city}</div>
                        <button class="relay-select-btn" onclick="selectChronopostRelay('${relay.id.replace(/'/g, "\\'").replace(/"/g, '&quot;')}', '${relay.name.replace(/'/g, "\\'")}', '${relay.address.replace(/'/g, "\\'")}', '${relay.zip}', '${relay.city.replace(/'/g, "\\'")}')">Choisir</button>
                    `;
                    listDiv.appendChild(card);
                }
            });
        } else {
            if (msgDiv) msgDiv.innerHTML = "<span style='color:#ff4444;'>Aucun point trouvé.</span>";
            if (listDiv) listDiv.innerHTML = "<div style='padding:20px; color:#c9d1d9; text-align:center;'>Aucun point relais disponible ici.</div>";
        }
    } catch (err) {
        if (msgDiv) msgDiv.innerHTML = "<span style='color:#ff4444;'>Erreur de connexion.</span>";
    }
}

// ==============================================================================

function selectChronopostRelay(id, name, address, zip, city) {
    const idField = document.getElementById('codeRelaisInput');
    const nameField = document.getElementById('relaisName');
    const addrField = document.getElementById('relaisAddress');
    const cpField = document.getElementById('relaisCP');
    const cityField = document.getElementById('relaisCity');

    if (idField) idField.value = id;
    if (nameField) nameField.value = name;
    if (addrField) addrField.value = address;
    if (cpField) cpField.value = zip;
    if (cityField) cityField.value = city;
    
    if (map) map.closePopup();
    
    [idField, cpField].forEach(f => {
        if (f) f.dispatchEvent(new Event('change', { bubbles: true }));
        if (f) f.dispatchEvent(new Event('input', { bubbles: true }));
    });

    const payBtn = document.getElementById('btn-pay-submit');
    if (payBtn) payBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initRelayMap();
    
    const zipInput = document.getElementById('mapZipInput');
    if (zipInput) {
        zipInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchRelays();
            }
        });
    }

    const countrySelect = document.getElementById('destinationCountry');
    if (countrySelect) {
        countrySelect.addEventListener('change', () => {
            const listDiv = document.getElementById('relayList');
            if (listDiv) listDiv.innerHTML = "<div style='padding:20px; text-align:center; color:#8b949e;'>Pays modifié. Entrez le code postal.</div>";
            const zipInput = document.getElementById('mapZipInput');
            if (zipInput) zipInput.value = "";
        });
    }
});
