const { chromium } = require('playwright');
const fs = require('fs');
const CFG = require('./config');
const { init, log } = require('./logger');
const { fetchLastCodeAndDelete } = require('./imap_a2f');
const { setupInterceptors, getToken } = require('./network');

(async () => {
    init();
    log("DEMARRAGE AUTOMATE (RAILWAY)", "SYSTEM", CFG.COLORS.MAGENTA);
    
    const browser = await chromium.launch({
        headless: true,
        args: ['--disable-blink-features=AutomationControlled', '--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await browser.newContext({ 
        userAgent: CFG.USER_AGENT, 
        viewport: CFG.VIEWPORT 
    });
    const page = await context.newPage();
    setupInterceptors(page);

    try {
        log("Navigation vers Flunch...", "NAV", CFG.COLORS.CYAN);
        await page.goto(CFG.URLS.LOGIN, { waitUntil: 'domcontentloaded', timeout: 60000 });
        
        // Gestion cookies
        try { await page.click(CFG.SELECTORS.COOKIE_OK, { timeout: 5000 }); } catch (e) {}

        log("Saisie des identifiants...", "AUTH", CFG.COLORS.CYAN);
        await page.click(CFG.SELECTORS.LOGIN_BTN);
        await page.waitForSelector(CFG.SELECTORS.EMAIL_INPUT);
        
        // On utilise fill pour plus de fiabilité sur serveur
        await page.fill(CFG.SELECTORS.EMAIL_INPUT, CFG.EMAIL);
        await page.fill(CFG.SELECTORS.PASS_INPUT, CFG.PASS);
        
        // On attend que le bouton ne soit plus grisé (disabled)
        await page.waitForFunction((selector) => {
            const btn = document.evaluate(selector.replace('xpath=', ''), document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            return btn && !btn.disabled;
        }, CFG.SELECTORS.SUBMIT_BTN, { timeout: 10000 }).catch(() => log("Bouton toujours désactivé, tentative forcée...", "AUTH", CFG.COLORS.YELLOW));

        await page.click(CFG.SELECTORS.SUBMIT_BTN);

        // Attente A2F
        try {
            await page.waitForSelector(CFG.SELECTORS.A2F_INPUT, { timeout: 15000 });
            log("Attente de l'email A2F (10s)...", "A2F", CFG.COLORS.YELLOW);
            await new Promise(r => setTimeout(r, 10000));
            const code = await fetchLastCodeAndDelete();
            if (code) {
                log(`Code trouvé : ${code}`, "A2F", CFG.COLORS.GREEN);
                await page.fill(CFG.SELECTORS.A2F_INPUT, code);
                await page.click(CFG.SELECTORS.A2F_SUBMIT);
            }
        } catch (e) {
            log("Pas d'A2F détecté ou timeout.", "A2F", CFG.COLORS.GREY);
        }

        // Navigation Profil pour trigger le token
        log("Navigation Profil pour capture token...", "NAV", CFG.COLORS.CYAN);
        await page.waitForTimeout(2000);
        
        // On n'attend plus 'networkidle' qui est trop capricieux
        await page.goto(CFG.URLS.PROFILE, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => log("Timeout partiel sur profil, on continue...", "NAV", CFG.COLORS.YELLOW));
        
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
        }
    } catch (err) {
        log(`CRASH AUTOMATE : ${err.message}`, "CRITICAL", CFG.COLORS.RED);
    } finally {
        await browser.close();
        log("Navigateur fermé.", "SYSTEM", CFG.COLORS.MAGENTA);
    }
})();
