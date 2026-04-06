const { chromium } = require('playwright');
const fs = require('fs');
const { HEADLESS, VIEWPORT, USER_AGENT, URLS, COLORS, TOKEN_FILE } = require('./config');
const { log, clearLog } = require('./logger');
const { takeScreenshot } = require('./screenshot');

const run = async () => {
    clearLog();
    const targetId = process.argv[2] || "Non spécifié";
    log(`Initialisation du système pour l'ID: ${targetId}...`, "SYSTEM", COLORS.CYAN, true);

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

        const token = await page.evaluate(() => localStorage.getItem('token'));
        if (token) {
            log("TOKEN RÉCUPÉRÉ AVEC SUCCÈS !", "SUCCESS", COLORS.GREEN, true);
            fs.appendFileSync(TOKEN_FILE, token + "\n", 'utf-8');
            log(`Sauvegardé (Historique) dans ${TOKEN_FILE}`, "SYSTEM", COLORS.GREY, false);
        } else {
            const cookies = await context.cookies();
            const authCookie = cookies.find(c => c.name.includes('token'));
            if (authCookie) {
                log("Token trouvé dans les cookies.", "SUCCESS", COLORS.GREEN, true);
                fs.appendFileSync(TOKEN_FILE, authCookie.value + "\n", 'utf-8');
            }
        }
        
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
