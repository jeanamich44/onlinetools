const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { 
    HEADLESS, VIEWPORT, USER_AGENT, URLS, COLORS, SELECTORS, EMAIL, PASS, PROXY 
} = require('./config');
const { log, clearLog } = require('./logger');
const { takeScreenshot } = require('./screenshot');

const BROWSER_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage'
];

const run = async () => {
    clearLog();
    const targetId = process.argv[2] || "Non spécifié";
    log(`[SERVEUR] Lancement du processus de connexion pour l'ID: ${targetId}`, "SYSTEM", COLORS.CYAN, true);


    const context = await browser.newContext({ viewport: VIEWPORT, userAgent: USER_AGENT });
    const page = await context.newPage();

    const shoot = async (name) => {
        const customPath = path.join(__dirname, 'output', `screenshot_${Date.now()}_${name}.png`);
        await takeScreenshot(page, customPath);
    };

    try {
        // [1] CHARGEMENT DE LA PAGE
        log("Chargement de la page de connexion...", "STEP", COLORS.MAGENTA, true);
        await page.goto(URLS.LOGIN, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await shoot("chargement_page");

        // [2] DELAI 4S
        log("Délai de 4s (stabilisation)...", "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, 4000));

        // [3] CLIQUER COOKIE_OK
        log("Clic sur 'OK pour moi' (Cookies)...", "ACTION", COLORS.CYAN, true);
        await page.click(SELECTORS.COOKIE_OK);
        await shoot("cookies_acceptes");

        // [4] DELAI 2S
        log("Délai de 2s...", "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, 2000));

        // [5] CLIQUER LOGIN_BTN
        log("Clic sur le bouton de connexion principal...", "ACTION", COLORS.CYAN, true);
        await page.click(SELECTORS.LOGIN_BTN);
        await shoot("clic_login_bouton");

        // [6] DELAI 5S
        log("Délai de 5s (chargement formulaire)...", "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, 5000));

        // [7] ECRIRE EMAIL
        log(`Saisie de l'email : ${EMAIL}`, "ACTION", COLORS.CYAN, true);
        await page.fill(SELECTORS.EMAIL_INPUT, EMAIL);
        await shoot("saisie_email");

        // [8] DELAI 3S
        log("Délai de 3s...", "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, 3000));

        // [9] ECRIRE PASS
        log("Saisie du mot de passe...", "ACTION", COLORS.CYAN, true);
        await page.fill(SELECTORS.PASS_INPUT, PASS);
        await shoot("saisie_pass");

        log("Formulaire de connexion rempli.", "SUCCESS", COLORS.GREEN, true);

    } catch (err) {
        log(`ERREUR DURANT LE PROCESSUS: ${err.message}`, "ERROR", COLORS.RED, true);
        await shoot("erreur_processus");
    }

    log("Script terminé. Browser maintenu ouvert pour inspection.", "SYSTEM", COLORS.CYAN, true);
};

run();
