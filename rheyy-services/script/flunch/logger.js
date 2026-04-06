const fs = require('fs');
const { LOG_FILE } = require('./config');

const init = () => {
    const separator = "=========================================================";
    const header = `[SYSTEM] SESSION DEMARREE LE : ${new Date().toLocaleString()}`;
    fs.appendFileSync(LOG_FILE, `\n${separator}\n${header}\n${separator}\n`);
};

const log = (msg, category, color = "") => {
    const time = new Date().toLocaleTimeString();
    const entry = `[${time}] [${category.padEnd(8)}] ${msg}`;
    
    // LOG FICHIER : On écrit TOUT pour le debug
    fs.appendFileSync(LOG_FILE, `${entry}\n`);

    // LOG CONSOLE (Railway) : On ne garde que l'essentiel et le Propre
    const consoleCategories = ["SYSTEM", "NAV", "AUTH", "A2F", "SUCCESS", "CRITICAL", "DELAY"];
    if (consoleCategories.includes(category.trim())) {
        console.log(`[${category.trim()}] ${msg}`);
    }
};

module.exports = { init, log };
