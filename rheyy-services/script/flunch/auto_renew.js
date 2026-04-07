const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { TOKEN_FILE } = require('./config');

// Paramètres
const CHECK_INTERVAL_MS = 60000; // Vérification chaque minute
const RENEW_THRESHOLD_MINUTES = 60; // 60 minutes avant expiration (1 heure)
let isRunning = false; // Booléen pour éviter de lancer le bot plusieurs fois en même temps

function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        if (!base64Url) return null;
        
        // Convertir base64url en base64 classique
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        // Décoder le buffer base64
        const jsonPayload = Buffer.from(base64, 'base64').toString('utf-8');
        return JSON.parse(jsonPayload);
    } catch (e) {
        console.error("Erreur de décodage JWT :", e.message);
        return null;
    }
}

function launchFlunchBot() {
    if (isRunning) {
        console.log("[AUTO-RENEW] Bot déjà en cours d'exécution, on ignore la requête de lancement.");
        return;
    }
    
    console.log(`[AUTO-RENEW] Lancement du bot de régénération (main.js)...`);
    isRunning = true;

    const botProcess = spawn('node', ['main.js', 'auto-renew'], {
        cwd: __dirname,
        stdio: 'inherit' // Affiche les logs du bot dans cette console
    });

    botProcess.on('close', (code) => {
        console.log(`[AUTO-RENEW] Processus bot terminé avec le code ${code}.`);
        isRunning = false;
    });
}

function checkTokenAndRenew() {
    try {
        if (!fs.existsSync(TOKEN_FILE)) {
            console.log(`[AUTO-RENEW] Fichier token introuvable (${TOKEN_FILE}).`);
            // Pas de token = on en crée un ? (Au choix, là on ne fait rien)
            return;
        }

        const lines = fs.readFileSync(TOKEN_FILE, 'utf8').split('\n').map(l => l.trim()).filter(l => l.length > 0);
        if (lines.length === 0) {
            console.log("[AUTO-RENEW] Le fichier token est vide.");
            return;
        }

        // On vérifie le TOUT DERNIER token ajouté
        const lastToken = lines[lines.length - 1];
        const payload = parseJwt(lastToken);

        if (payload && payload.exp) {
            const expTimeMs = payload.exp * 1000;
            const nowMs = Date.now();
            const diffMinutes = (expTimeMs - nowMs) / (1000 * 60);

            console.log(`[AUTO-RENEW] Expiration du dernier token dans : ${Math.round(diffMinutes)} minutes.`);

            if (diffMinutes <= RENEW_THRESHOLD_MINUTES) {
                console.log(`[AUTO-RENEW] Seuil critique atteint (<= ${RENEW_THRESHOLD_MINUTES} min). Trigger de la régénération...`);
                launchFlunchBot();
            } else {
                console.log("[AUTO-RENEW] Le token est toujours valide, aucune action requise.");
            }
        } else {
            console.log("[AUTO-RENEW] Impossible d'extraire la date d'expiration (exp) de ce token.");
        }
    } catch (e) {
        console.error("[AUTO-RENEW] Erreur lors de la vérification :", e);
    }
}

// Lancement Boucle
console.log(`[AUTO-RENEW] Service démarré. Vérification du token toutes les ${CHECK_INTERVAL_MS / 1000}s avec un seuil de ${RENEW_THRESHOLD_MINUTES}min.`);
checkTokenAndRenew(); // Faire un premier check au lancement
setInterval(checkTokenAndRenew, CHECK_INTERVAL_MS);
