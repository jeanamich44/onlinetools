const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { 
    HEADLESS, VIEWPORT, USER_AGENT, URLS, COLORS, SELECTORS, EMAIL, PASS, PROXIES 
} = require('./config');
const { log, clearLog } = require('./logger');
const { takeScreenshot } = require('./screenshot');
const { fetchLastCodeAndDelete } = require('./imap_a2f');

const BROWSER_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage'
];

/**
 * Simule une frappe humaine caractère par caractère avec logs et délais aléatoires.
 */
const humanType = async (page, selector, text, fieldName) => {
    log(`Début de saisie humaine pour ${fieldName}...`, "STEP", COLORS.MAGENTA, true);
    
    // On s'assure que le champ est prêt
    await page.waitForSelector(selector, { state: 'visible', timeout: 15000 });
    await page.focus(selector);

    for (let i = 0; i < text.length; i++) {
        const char = text[i];
        await page.keyboard.type(char);
        
        // Log du caractère saisi (on cache le caractère si c'est un mot de passe pour la sécurité)
        const displayChar = fieldName.toLowerCase().includes('pass') ? '*' : char;
        log(`[${fieldName}] Saisie : '${displayChar}' (${i + 1}/${text.length})`, "TRACE", COLORS.GREY, false);
        
        // Délai aléatoire entre 100ms et 350ms
        await new Promise(r => setTimeout(r, Math.random() * (350 - 100) + 100));
    }
    
    log(`${fieldName} saisi avec succès.`, "OK", COLORS.GREEN, true);
};

const run = async () => {
    clearLog();
    const targetId = process.argv[2] || "Non spécifié";
    log(`[SERVEUR] Lancement du processus de connexion pour l'ID: ${targetId}`, "SYSTEM", COLORS.CYAN, true);

    // Choix aléatoire d'un proxy dans la liste
    const proxyConfig = PROXIES && PROXIES.length > 0 
        ? PROXIES[Math.floor(Math.random() * PROXIES.length)] 
        : null;

    if (proxyConfig) {
        log(`[PROXY] Utilisation du proxy: ${proxyConfig.server.substring(proxyConfig.server.lastIndexOf(':')+1)}`, "INFO", COLORS.CYAN, true);
    } else {
        log(`[PROXY] Aucun proxy configuré.`, "INFO", COLORS.YELLOW, true);
    }

    const browser = await chromium.launch({ 
        headless: HEADLESS, 
        args: BROWSER_ARGS,
        proxy: proxyConfig ? {
            server: proxyConfig.server,
            username: proxyConfig.username,
            password: proxyConfig.password
        } : undefined
    });

    const context = await browser.newContext({ viewport: VIEWPORT, userAgent: USER_AGENT });
    const page = await context.newPage();

    const shoot = async (name) => {
        const screenshotName = `screenshot_${Date.now()}_${name}.png`;
        const outputDir = path.join(__dirname, 'output');
        const customPath = path.join(outputDir, screenshotName);
        await takeScreenshot(page, customPath);
    };

    try {
        // [0] VERIFICATION IP
        log("Vérification de l'IP du Proxy...", "STEP", COLORS.MAGENTA, true);
        await page.goto(URLS.IP_TEST, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await shoot("0_verification_ip");
        await new Promise(r => setTimeout(r, 2000)); // Petit délai de lecture

        // [1] CHARGEMENT DE LA PAGE
        log("Chargement de la page de connexion Flunch...", "STEP", COLORS.MAGENTA, true);
        await page.goto(URLS.LOGIN, { waitUntil: 'domcontentloaded', timeout: 30000 });

        // [2] DELAI 4S
        log("Délai de 4s (stabilisation)...", "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, 4000));

        // [3] CLIQUER COOKIE_OK
        log("Clic sur 'OK pour moi' (Cookies)...", "ACTION", COLORS.CYAN, true);
        await page.click(SELECTORS.COOKIE_OK);

        // [4] DELAI 2S
        log("Délai de 2s...", "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, 2000));

        // [5] CLIQUER LOGIN_BTN
        log("Clic sur le bouton de connexion principal...", "ACTION", COLORS.CYAN, true);
        await page.click(SELECTORS.LOGIN_BTN);

        // [6] DELAI 5S
        log("Délai de 5s (chargement formulaire)...", "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, 5000));

        // [7] SAISIE HUMAINE EMAIL
        await humanType(page, SELECTORS.EMAIL_INPUT, EMAIL, "EMAIL");

        // [8] DELAI 3S
        log("Délai de 3s...", "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, 3000));

        // [9] SAISIE HUMAINE PASS
        await humanType(page, SELECTORS.PASS_INPUT, PASS, "PASSWORD");
        await shoot("5_saisie_pass_terminee");

        // [10] CLIC SUBMIT_BTN
        log("Clic sur Se Connecter...", "ACTION", COLORS.CYAN, true);
        await page.click(SELECTORS.SUBMIT_BTN);
        
        // [11] DELAI 3S (attente de l'A2F ou chargement)
        log("Délai de 3s...", "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, 3000));
        await shoot("6_a2f_page");

        log("Formulaire de connexion envoyé. Vérification IMAP pour l'A2F...", "STEP", COLORS.MAGENTA, true);

        // [12] RECUPERATION CODE IMAP (Boucle de 60 secondes max)
        let a2fCode = null;
        for (let attempt = 1; attempt <= 12; attempt++) {
            log(`Tentative IMAP numéro ${attempt}/12...`, "INFO", COLORS.YELLOW, true);
            a2fCode = await fetchLastCodeAndDelete();
            if (a2fCode) {
                break;
            }
            await new Promise(r => setTimeout(r, 5000)); // Attendre 5s entre chaque essai
        }

        if (!a2fCode) {
            log("Délai d'attente du mail expiré après 60 secondes.", "ERROR", COLORS.RED, true);
            throw new Error("Timeout A2F Email");
        }

        log("Processus terminé avec succès, code récupéré.", "SUCCESS", COLORS.GREEN, true);

    } catch (err) {
        log(`ERREUR DURANT LE PROCESSUS: ${err.message}`, "ERROR", COLORS.RED, true);
        await shoot("erreur_processus");
    }

    log("Script terminé. Browser maintenu ouvert pour inspection.", "SYSTEM", COLORS.CYAN, true);
};

run();
