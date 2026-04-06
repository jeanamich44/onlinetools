const fs = require('fs');
const { LOG_FILE, COLORS } = require('./config');

let startTime = Date.now();

const init = () => {
    startTime = Date.now();
    const d = new Date();
    const header = `\n============================================================\n--- SESSION ${d.toLocaleString('fr-FR')} ---\n============================================================\n`;
    fs.appendFileSync(LOG_FILE, header, 'utf8');
};

const log = (msg, category, color = COLORS.RESET, verboseOnly = false) => {
    const time = ((Date.now() - startTime) / 1000).toFixed(2);
    const logEntry = `[${time}s] [${category}] ${msg}`;
    const fileEntry = `[${new Date().toISOString()}] ${logEntry}`;

    if (!verboseOnly) {
        console.log(`${color}${logEntry}${COLORS.RESET}`);
    }
    fs.appendFileSync(LOG_FILE, fileEntry + "\n", 'utf8');
};

const logToFile = (content) => {
    fs.appendFileSync(LOG_FILE, content, 'utf8');
};

module.exports = { init, log, logToFile };
