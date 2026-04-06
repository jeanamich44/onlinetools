const { chromium } = require('playwright');
const fs = require('fs');
const CFG = require('./config');
const { init, log } = require('./logger');
const { fetchLastCodeAndDelete } = require('./imap_a2f');
const { setupInterceptors, getToken, getSessionTokens } = require('./network');

(async () => {
    init();
    log("DEMARRAGE AUTOMATE (RAILWAY)", "SYSTEM", CFG.COLORS.MAGENTA);
    
    const SCREEN_DIR = './screenshots';
    if (!fs.existsSync(SCREEN_DIR)) fs.mkdirSync(SCREEN_DIR);

    const browser = await chromium.launch({
        headless: true,
        args: ['--disable-blink-features=AutomationControlled', '--no-sandbox', '--disable-setuid-sandbox', '--window-size=1280,1024']
    });
    const context = await browser.newContext({
        userAgent: CFG.USER_AGENT,
        viewport: { width: 1280, height: 1024 }
    });
    const page = await context.newPage();
    setupInterceptors(page);

    const takeScreen = async (name) => {
        const path = `${SCREEN_DIR}/${Date.now()}_${name}.png`;
        await page.screenshot({ path });
        log(`📸 Screenshot: ${name}`, "SYSTEM", CFG.COLORS.MAGENTA);
    };

    try {
        log("Navigation vers Flunch...", "NAV", CFG.COLORS.CYAN);
        await page.goto(CFG.URLS.LOGIN, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await takeScreen("1_LOGIN_PAGE");

        // Gestion cookies
        try { 
            await page.click(CFG.SELECTORS.COOKIE_OK, { timeout: 5000 }); 
            await takeScreen("2_COOKIES_CLICKED");
        } catch (e) { }

        log("Saisie des identifiants...", "AUTH", CFG.COLORS.CYAN);
        await page.click(CFG.SELECTORS.LOGIN_BTN).catch(() => { });

        // On attend juste que le champ soit greffé au code source (même s'il se cache)
        await page.waitForSelector(CFG.SELECTORS.EMAIL_INPUT, { state: 'attached', timeout: 30000 });

        try {
            // Tentative 1 : Frappe Humaine Naturelle avec LOGS
            log("Saisie Email...", "AUTH");
            await page.focus(CFG.SELECTORS.EMAIL_INPUT);
            for (const char of CFG.EMAIL) {
                await page.keyboard.type(char, { delay: 50 });
                log(`Tape Email: ${char}`, "AUTH");
            }
            
            log("Saisie Password...", "AUTH");
            await page.focus(CFG.SELECTORS.PASS_INPUT);
            for (const char of CFG.PASS) {
                await page.keyboard.type(char, { delay: 50 });
                log(`Tape Pass: *`, "AUTH");
            }
        } catch (e) {
            log("Champs masqués par la page, injection Clic Fantôme (DOM)...", "AUTH", CFG.COLORS.YELLOW);
            await page.evaluate(({ email, pass, selEmail, selPass }) => {
                const getByXpath = (path) => document.evaluate(path.replace('xpath=', ''), document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                const emailNode = getByXpath(selEmail);
                const passNode = getByXpath(selPass);
                if (emailNode) { emailNode.value = email; emailNode.dispatchEvent(new Event('input', { bubbles: true })); emailNode.dispatchEvent(new Event('change', { bubbles: true })); }
                if (passNode) { passNode.value = pass; passNode.dispatchEvent(new Event('input', { bubbles: true })); passNode.dispatchEvent(new Event('change', { bubbles: true })); }
            }, { email: CFG.EMAIL, pass: CFG.PASS, selEmail: CFG.SELECTORS.EMAIL_INPUT, selPass: CFG.SELECTORS.PASS_INPUT });
        }

        log("Délai : +1s avant la vérification du bouton submit", "DELAY", CFG.COLORS.GREY);
        await page.waitForTimeout(1000);

        // Le seul problème du début : on attend juste que le bouton s'active
        await page.waitForFunction((selector) => {
            const btn = document.evaluate(selector.replace('xpath=', ''), document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            return btn && !btn.disabled;
        }, CFG.SELECTORS.SUBMIT_BTN, { timeout: 15000 }).catch(() => log("Bouton gris, clic forcé...", "AUTH", CFG.COLORS.YELLOW));

        log("Délai : +1s avant le clic sur validation", "DELAY", CFG.COLORS.GREY);
        await page.waitForTimeout(1000);
        await takeScreen("3_BEFORE_SUBMIT");

        try {
            log("Tentative 1 : Clic Fantôme (Exécution Javascript Native)...", "AUTH", CFG.COLORS.CYAN);
            await page.evaluate((selSubmit) => {
                const btn = document.evaluate(selSubmit.replace('xpath=', ''), document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (!btn) throw new Error("Noeud introuvable dans le DOM");
                btn.removeAttribute('disabled');
                btn.click();
            }, CFG.SELECTORS.SUBMIT_BTN);
        } catch (err) {
            log(`Échec du Clic Fantôme, Tentative 2 : Feinte Clavier (Touche Entrée)...`, "AUTH", CFG.COLORS.YELLOW);
            await page.focus(CFG.SELECTORS.PASS_INPUT).catch(() => { });
            await page.keyboard.press('Enter');
        }


        // Attente A2F
        try {
            // Attachement simple pour éviter les faux positifs 'invisible'
            await page.waitForSelector(CFG.SELECTORS.A2F_INPUT, { state: 'attached', timeout: 15000 });
            log("Attente de l'email A2F (+1s -> 11s)...", "A2F", CFG.COLORS.YELLOW);
            log("Délai : Pause de 11000ms", "DELAY", CFG.COLORS.GREY);
            await new Promise(r => setTimeout(r, 11000));
            const code = await fetchLastCodeAndDelete();
            if (code) {
                log(`Code trouvé : ${code}`, "A2F", CFG.COLORS.GREEN);

                try {
                    // Feinte Clavier Principale avec LOGS
                    log("Saisie Code A2F...", "A2F");
                    await page.focus(CFG.SELECTORS.A2F_INPUT);
                    for (const char of code) {
                        await page.keyboard.type(char, { delay: 50 });
                        log(`Tape Code: ${char}`, "A2F");
                    }
                } catch (err) {
                    log("Champ A2F masqué, injection Clic Fantôme (DOM)...", "A2F", CFG.COLORS.YELLOW);
                    await page.evaluate(({ c, sel }) => {
                        const getByXpath = (path) => document.evaluate(path.replace('xpath=', ''), document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        const inputNode = getByXpath(sel);
                        if (inputNode) { inputNode.value = c; inputNode.dispatchEvent(new Event('input', { bubbles: true })); }
                    }, { c: code, sel: CFG.SELECTORS.A2F_INPUT });
                }

                log("Délai : +1s avant le clic validation A2F", "DELAY", CFG.COLORS.GREY);
                await page.waitForTimeout(1000);
                await takeScreen("4_A2F_TYPED");

                // Moteur hybride : Clic Fantôme puis Frappe
                try {
                    log("Tentative A2F 1 : Clic Fantôme...", "A2F", CFG.COLORS.CYAN);
                    await page.evaluate((selA2FSubmit) => {
                        const btn = document.evaluate(selA2FSubmit.replace('xpath=', ''), document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        if (!btn) throw new Error("Noeud introuvable A2F");
                        btn.removeAttribute('disabled');
                        btn.click();
                    }, CFG.SELECTORS.A2F_SUBMIT);
                } catch (err) {
                    log("Échec Clic Fantôme A2F, Tentative 2 : Feinte clavier...", "A2F", CFG.COLORS.YELLOW);
                    await page.focus(CFG.SELECTORS.A2F_INPUT).catch(() => { });
                    await page.keyboard.press('Enter');
                }
            }
        } catch (e) {
            log("Pas d'A2F détecté ou timeout.", "A2F", CFG.COLORS.GREY);
        }

        // Navigation Profil pour trigger le token
        log("Navigation Profil pour capture token...", "NAV", CFG.COLORS.CYAN);
        await takeScreen("5_POST_LOGIN");

        log("Délai : Pause de 3000ms (+1s)", "DELAY", CFG.COLORS.GREY);
        await page.waitForTimeout(3000);

        // On n'attend plus 'networkidle' qui est trop capricieux
        await page.goto(CFG.URLS.PROFILE, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => log("Timeout partiel sur profil, on continue...", "NAV", CFG.COLORS.YELLOW));
        await takeScreen("6_PROFILE_PAGE");

        let wait = 0;
        // On surveille le token pendant 15 secondes max
        while (!getToken() && wait < 15) {
            await page.waitForTimeout(1000);
            wait++;
        }

        const captured = getToken();
        if (captured) {
            fs.writeFileSync(CFG.TOKEN_FILE, captured);
            log("Token sauvegardé avec succès.", "SUCCESS", CFG.COLORS.GREEN);
        } else {
            log("Échec de la capture du token.", "ERROR", CFG.COLORS.RED);
            await takeScreen("ERROR_NO_TOKEN");
        }
    } catch (err) {
        log(`CRASH AUTOMATE : ${err.message}`, "CRITICAL", CFG.COLORS.RED);
        await takeScreen("CRASH_DUMP");
    } finally {
        // Log de tous les tokens trouvés
        const allTokens = getSessionTokens();
        log(`--- RÉCAPITULATIF DES TOKENS VUS (${allTokens.length}) ---`, "DEBUG");
        allTokens.forEach((t, i) => {
            log(`TOKEN ${i + 1} [Longueur: ${t.length}] : ${t}`, "DEBUG");
        });
        log(`-----------------------------------------------`, "DEBUG");

        await browser.close();
        log("Navigateur fermé.", "SYSTEM", CFG.COLORS.MAGENTA);
    }
})();
