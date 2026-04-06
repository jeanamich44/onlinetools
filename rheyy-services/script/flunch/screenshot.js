const { SCREENSHOT, COLORS } = require('./config');
const { log } = require('./logger');

const takeScreenshot = async (page) => {
    try {
        log("Capturing d'écran en cours...", "TRACE", COLORS.GREY, false);
        await page.screenshot({ path: SCREENSHOT });
        log("Screenshot enregistré avec succès.", "SUCCESS", COLORS.GREEN, true);
    } catch (err) {
        log(`Erreur Screenshot: ${err.message}`, "ERROR", COLORS.RED, true);
    }
};

module.exports = { takeScreenshot };
