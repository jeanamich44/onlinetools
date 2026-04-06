const { chromium } = require('playwright');
const { HEADLESS, VIEWPORT, USER_AGENT, URLS, COLORS } = require('./config');
const { log, clearLog } = require('./logger');
const { takeScreenshot } = require('./screenshot');

const run = async () => {
    clearLog();
    log("Initialisation du système...", "SYSTEM", COLORS.CYAN, true);

    log(`Lancement de Chromium (Headless: ${HEADLESS})`, "TRACE", COLORS.GREY, false);
    
    const startTime = Date.now();
    const browser = await chromium.launch({ 
        headless: HEADLESS,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    log(`Navigateur lancé en ${Date.now() - startTime}ms`, "TRACE", COLORS.GREY, false);

    const context = await browser.newContext({
        viewport: VIEWPORT,
        userAgent: USER_AGENT
    });
    log("Contexte de navigation créé.", "TRACE", COLORS.GREY, false);

    const page = await context.newPage();

    try {
        log(`Ouverture de la page de connexion: ${URLS.LOGIN}...`, "STEP", COLORS.MAGENTA, true);
        
        const navStart = Date.now();
        await page.goto(URLS.LOGIN, { waitUntil: 'networkidle' });
        
        log(`Délai de navigation: ${Date.now() - navStart}ms`, "TRACE", COLORS.GREY, false);
        
        log("Page Flunch chargée avec succès.", "SUCCESS", COLORS.GREEN, true);
        
        await takeScreenshot(page);
        
        log("Attente de stabilisation de la page (3s)...", "TRACE", COLORS.GREY, false);
        await page.waitForTimeout(3000);
        
    } catch (err) {
        log(`ERREUR CRITIQUE: ${err.message}`, "ERROR", COLORS.RED, true);
    } finally {
        await browser.close();
        log("Fermeture du navigateur.", "SYSTEM", COLORS.CYAN, true);
        log("Session terminée.", "TRACE", COLORS.GREY, false);
    }
};

run();
