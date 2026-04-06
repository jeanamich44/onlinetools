const { chromium } = require('playwright');
const fs = require('fs');
const { 
    HEADLESS, VIEWPORT, USER_AGENT, URLS, COLORS 
} = require('./config');
const { log, clearLog } = require('./logger');
const { takeScreenshot } = require('./screenshot');

// Args optimisés Railway (stables)
const BROWSER_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage'
];

const run = async () => {
    // On vide l'ancien log au démarrage
    clearLog();
    
    const targetId = process.argv[2] || "Non spécifié";
    log(`[SERVEUR] Initialisation debug screenshot pour l'ID: ${targetId}`, "SYSTEM", COLORS.CYAN, true);

    log("Lancement de Chromium...", "TRACE", COLORS.GREY, false);
    const browser = await chromium.launch({
        headless: HEADLESS,
        args: BROWSER_ARGS
    });

    const context = await browser.newContext({
        viewport: VIEWPORT,
        userAgent: USER_AGENT
    });

    const page = await context.newPage();
    log("Navigateur et page prêts.", "TRACE", COLORS.GREY, false);

    try {
        log(`Navigation vers la page Flunch...`, "STEP", COLORS.MAGENTA, true);
        
        const navStart = Date.now();
        // domcontentloaded pour éviter de bloquer sur les trackers/scripts tiers
        await page.goto(URLS.LOGIN, { waitUntil: 'domcontentloaded', timeout: 30000 });
        
        log(`Page HTML chargée (${Date.now() - navStart}ms).`, "OK", COLORS.GREEN, true);

        log("Attente de 3s pour la stabilisation visuelle...", "TRACE", COLORS.GREY, true);
        await new Promise(r => setTimeout(r, 3000));

        log("Prise de la capture d'écran de debug...", "STEP", COLORS.YELLOW, true);
        await takeScreenshot(page);
        
        log("Opération terminée avec succès.", "SUCCESS", COLORS.GREEN, true);

    } catch (err) {
        log(`ERREUR DURANT LE DEBUG: ${err.message}`, "ERROR", COLORS.RED, true);
    }
    
    // browser.close() retiré pour maintenir la page ouverte si besoin
    log("Script terminé. Page non fermée.", "SYSTEM", COLORS.CYAN, true);
};

run();
