const { SCREENSHOT, COLORS } = require('./config');
const { log } = require('./logger');
const path = require('path');

const takeScreenshot = async (page, customPath = null) => {
    try {
        const targetPath = customPath || SCREENSHOT;
        log(`Capture d'écran (${path.basename(targetPath)}) en cours...`, "TRACE", COLORS.GREY, false);
        await page.screenshot({ path: targetPath });
        log("Screenshot enregistré avec succès.", "SUCCESS", COLORS.GREEN, true);
    } catch (err) {
        log(`Erreur Screenshot: ${err.message}`, "ERROR", COLORS.RED, true);
    }
};

module.exports = { takeScreenshot };
