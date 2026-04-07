const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { 
    HEADLESS, VIEWPORT, USER_AGENT, URLS, COLORS, SELECTORS, EMAIL, PASS, PROXIES, DELAYS, TOKEN_FILE 
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
        
        // Log du caractère saisi
        log(`[${fieldName}] Saisie : '${char}' (${i + 1}/${text.length})`, "TRACE", COLORS.GREY, false);
        
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
        log("Vérification de l'IP du Proxy...", "STEP", COLORS.MAGENTA, false);
        await page.goto(URLS.IP_TEST, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await shoot("0_verification_ip");
        await new Promise(r => setTimeout(r, DELAYS.POST_IP_TEST)); // Petit délai de lecture

        // [1] CHARGEMENT DE LA PAGE
        log("Chargement de la page de connexion Flunch...", "STEP", COLORS.MAGENTA, false);
        await page.goto(URLS.LOGIN, { waitUntil: 'domcontentloaded', timeout: 30000 });

        // [2] DELAI POST_HOMEPAGE
        log(`Délai de ${DELAYS.POST_HOMEPAGE / 1000}s (stabilisation)...`, "WAIT", COLORS.YELLOW, false);
        await new Promise(r => setTimeout(r, DELAYS.POST_HOMEPAGE));

        // [3] CLIQUER COOKIE_OK
        log("Clic sur 'OK pour moi' (Cookies)...", "ACTION", COLORS.CYAN, false);
        await page.click(SELECTORS.COOKIE_OK);

        // [4] DELAI POST_COOKIE
        log(`Délai de ${DELAYS.POST_COOKIE / 1000}s...`, "WAIT", COLORS.YELLOW, false);
        await new Promise(r => setTimeout(r, DELAYS.POST_COOKIE));

        // [5] CLIQUER LOGIN_BTN
        log("Clic sur le bouton de connexion principal...", "ACTION", COLORS.CYAN, false);
        await page.click(SELECTORS.LOGIN_BTN);

        // [6] DELAI POST_LOGIN_FORM_OPEN
        log(`Délai de ${DELAYS.POST_LOGIN_FORM_OPEN / 1000}s (chargement formulaire)...`, "WAIT", COLORS.YELLOW, false);
        await new Promise(r => setTimeout(r, DELAYS.POST_LOGIN_FORM_OPEN));

        // [7] SAISIE HUMAINE EMAIL
        await humanType(page, SELECTORS.EMAIL_INPUT, EMAIL, "EMAIL");

        // [8] DELAI POST_EMAIL_INPUT
        log(`Délai de ${DELAYS.POST_EMAIL_INPUT / 1000}s...`, "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, DELAYS.POST_EMAIL_INPUT));

        // [9] SAISIE HUMAINE PASS
        await humanType(page, SELECTORS.PASS_INPUT, PASS, "PASSWORD");
        await shoot("5_saisie_pass_terminee");

        // [10] CLIC SUBMIT_BTN
        log("Clic sur Se Connecter...", "ACTION", COLORS.CYAN, true);
        await page.click(SELECTORS.SUBMIT_BTN);
        
        // [11] DELAI POST_SUBMIT_LOGIN
        log(`Délai de ${DELAYS.POST_SUBMIT_LOGIN / 1000}s...`, "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, DELAYS.POST_SUBMIT_LOGIN));
        await shoot("6_a2f_page");

        log("Formulaire de connexion envoyé. Vérification IMAP pour l'A2F...", "STEP", COLORS.MAGENTA, true);

        // [12] RECUPERATION CODE IMAP (Boucle réduite à 3 max)
        let a2fCode = null;
        for (let attempt = 1; attempt <= 3; attempt++) {
            log(`Tentative IMAP numéro ${attempt}/3...`, "INFO", COLORS.YELLOW, true);
            a2fCode = await fetchLastCodeAndDelete();
            if (a2fCode) {
                break;
            }
            await new Promise(r => setTimeout(r, DELAYS.IMAP_RETRY));
        }

        if (!a2fCode) {
            log("Délai d'attente du mail expiré après 60 secondes.", "ERROR", COLORS.RED, true);
            throw new Error("Timeout A2F Email");
        }

        log("Processus IMAP terminé, code récupéré.", "SUCCESS", COLORS.GREEN, true);

        // [13] SAISIE DU CODE A2F
        await humanType(page, SELECTORS.A2F_INPUT, a2fCode, "A2F_CODE");

        // [14] SUBMIT DU CODE A2F
        log("Clic sur la validation du code...", "ACTION", COLORS.CYAN, true);
        await page.click(SELECTORS.A2F_SUBMIT);

        // [15] DELAI POST_A2F_SUBMIT
        log(`Délai de ${DELAYS.POST_A2F_SUBMIT / 1000}s (validation A2F)...`, "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, DELAYS.POST_A2F_SUBMIT));
        await shoot("7_dashboard_final");

        log("Connexion au compte réussie !", "SUCCESS", COLORS.GREEN, true);

        // [16] NAVIGATION PROFILE
        log("Navigation vers la page Profile...", "STEP", COLORS.MAGENTA, true);
        await page.goto(URLS.PROFILE, { waitUntil: 'domcontentloaded', timeout: 30000 });

        // [17] DELAI POST_PROFILE_NAV
        log(`Délai de ${DELAYS.POST_PROFILE_NAV / 1000}s sur le Profil...`, "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, DELAYS.POST_PROFILE_NAV));
        await shoot("8_page_profil");

        // [18] INTERCEPTION REQUETE ET CLIC PROFIL
        log("Attente de la requête API update_client_data...", "STEP", COLORS.MAGENTA, true);
        
        const requestPromise = page.waitForRequest(
            request => request.url().includes('update_client_data'),
            { timeout: 15000 }
        ).catch(() => null);

        log("Clic sur le bouton cible dans le profil...", "ACTION", COLORS.CYAN, true);
        await page.click(SELECTORS.PROFILE_ACTION_BTN);

        const apiRequest = await requestPromise;

        if (apiRequest) {
            log("Requête API interceptée, analyse du header Authorization...", "INFO", COLORS.YELLOW, true);
            const headers = await apiRequest.allHeaders();
            const authHeader = headers['authorization'];
            
            if (authHeader && authHeader.toLowerCase().startsWith('bearer ')) {
                const token = authHeader.substring(7).trim();
                fs.appendFileSync(TOKEN_FILE, token + "\n");
                
                if (token.length >= 730 && token.length <= 780) {
                    log(`TOKEN VALIDÉ ET SAUVEGARDÉ (${token.length} caractères)`, "SUCCESS", COLORS.GREEN, true);
                } else {
                    log(`Token sauvegardé, mais sa longueur est atypique (${token.length} caractères)`, "TRACE", COLORS.YELLOW, true);
                }
            } else {
                log("Header Authorization 'Bearer' introuvable dans la requête.", "ERROR", COLORS.RED, true);
            }
        } else {
            log("Aucune requête contenant 'update_client_data' interceptée.", "ERROR", COLORS.RED, true);
        }

        log(`Délai de ${DELAYS.POST_PROFILE_ACTION / 1000}s...`, "WAIT", COLORS.YELLOW, true);
        await new Promise(r => setTimeout(r, DELAYS.POST_PROFILE_ACTION));
        await shoot("9_page_profil_fin");

        log("Processus Automatisé Flunch entièrement terminé.", "SUCCESS", COLORS.GREEN, true);

    } catch (err) {
        log(`ERREUR DURANT LE PROCESSUS: ${err.message}`, "ERROR", COLORS.RED, true);
        await shoot("erreur_processus");
    }

    log("Script terminé. Browser maintenu ouvert pour inspection.", "SYSTEM", COLORS.CYAN, true);
};

run();
