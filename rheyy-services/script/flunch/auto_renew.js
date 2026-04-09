const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { TOKEN_FILE } = require('./config');

/**
 * CONFIGURATION
 */
const CHECK_INTERVAL_MS = 30 * 60 * 1000; // Vérification toutes les 30 minutes
const RENEW_THRESHOLD_MINUTES = 60;        // Seuil d'anticipation (1 heure)
const AUTO_RENEW_LOG = path.join(__dirname, 'logs', 'auto_renew_service.log');

let isRunning = false;

/**
 * LOGGING PERSONNALISÉ (Console + Fichier)
 */
function logService(msg, type = "INFO") {
    const timestamp = new Date().toLocaleString();
    const cleanMsg = `[${timestamp}] [${type}] ${msg}`;
    console.log(cleanMsg);
    
    try {
        if (!fs.existsSync(path.dirname(AUTO_RENEW_LOG))) fs.mkdirSync(path.dirname(AUTO_RENEW_LOG), { recursive: true });
        fs.appendFileSync(AUTO_RENEW_LOG, cleanMsg + "\n");
    } catch(e) {}
}

/**
 * PARSEUR JWT
 */
function parseJwt(token) {
    try {
        const parts = token.split('.');
        if (parts.length < 2) return null;
        const base64Url = parts[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = Buffer.from(base64, 'base64').toString('utf-8');
        return JSON.parse(jsonPayload);
    } catch (e) {
        logService("Erreur décodage JWT: " + e.message, "ERROR");
        return null;
    }
}

/**
 * LANCEMENT DU BOT
 */
function launchFlunchBot() {
    if (isRunning) {
        logService("Bot déjà actif, skipping.", "WARN");
        return;
    }
    
    logService("DÉMARRAGE DE LA RÉGÉNÉRATION (main.js)...", "ACTION");
    isRunning = true;

    // On lance main.js
    const botProcess = spawn('node', ['main.js'], {
        cwd: __dirname,
        stdio: 'inherit'
    });

    botProcess.on('error', (err) => {
        logService("Erreur fatale lors du lancement de node main.js: " + err.message, "CRITICAL");
        isRunning = false;
    });

    botProcess.on('close', (code) => {
        logService(`Processus bot terminé (Code: ${code})`, "FINISH");
        isRunning = false;
    });
}

/**
 * ANALYSE ET DÉCISION
 */
function checkTokenAndRenew() {
    logService("Vérification de l'état du token...", "CHECK");
    
    try {
        if (!fs.existsSync(TOKEN_FILE)) {
            logService("Fichier token absent ! Lancement initial requis.", "WARN");
            launchFlunchBot();
            return;
        }

        const raw = fs.readFileSync(TOKEN_FILE, 'utf8').trim();
        const lines = raw.split('\n').map(l => l.trim()).filter(l => l.length > 50); // Filtre les lignes trop courtes (pas de tokens)

        if (lines.length === 0) {
            logService("Fichier token vide. Lancement initial...", "WARN");
            launchFlunchBot();
            return;
        }

        const lastToken = lines[lines.length - 1];
        const payload = parseJwt(lastToken);

        if (!payload || !payload.exp) {
            logService("Token invalide ou sans date d'expiration. Régénération forcée.", "ERROR");
            launchFlunchBot();
            return;
        }

        const expTimeMs = payload.exp * 1000;
        const nowMs = Date.now();
        const diffMinutes = (expTimeMs - nowMs) / (1000 * 60);

        logService(`Le dernier token expire dans ${Math.round(diffMinutes)} min.`);

        if (diffMinutes <= RENEW_THRESHOLD_MINUTES) {
            logService(`SEUIL ATTEINT (<= ${RENEW_THRESHOLD_MINUTES} min). Déclenchement !`, "TRIGGER");
            launchFlunchBot();
        } else {
            logService("Token OK. Aucune action.", "SLEEP");
        }

    } catch (e) {
        logService("Erreur lors du check : " + e.message, "ERROR");
    }
}

// Initialisation
logService("============== SERVICE AUTO-RENEW DÉMARRÉ ==============", "SYSTEM");
checkTokenAndRenew(); 
setInterval(checkTokenAndRenew, CHECK_INTERVAL_MS);
