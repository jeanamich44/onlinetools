const fs = require('fs');
const { LOG_FILE } = require('./config');

const init = () => {
    const separator = "=========================================================";
    const header = `[SYSTEM] SESSION DEMARREE LE : ${new Date().toLocaleString()}`;
    fs.appendFileSync(LOG_FILE, `\n${separator}\n${header}\n${separator}\n`);
};

const log = (msg, category, color = "") => {
    // Format : [15:30:05] [CATEGORIE] Message
    const time = new Date().toLocaleTimeString();
    const entry = `[${time}] [${category.padEnd(8)}] ${msg}`;
    
    console.log(entry); // Console pour Railway
    fs.appendFileSync(LOG_FILE, `${entry}\n`); // Fichier pour l'interface Admin
};

module.exports = { init, log };
