const fs = require('fs');
const { LOG_FILE, COLORS } = require('./config');

const log = (message, tag = "SYSTEM", color = COLORS.CYAN, showInConsole = true) => {
    const now = new Date();
    const time = now.toLocaleTimeString('en-US', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const date = now.toLocaleDateString('fr-FR');

    const fileLine = `[${date} ${time}] [${tag}] ${message}\n`;
    fs.appendFileSync(LOG_FILE, fileLine, 'utf-8');

    if (showInConsole) {
        const consoleLine = `${COLORS.GREY}[${time}]${COLORS.RESET} ${color}[${tag}]${COLORS.RESET} ${message}`;
        console.log(consoleLine);
    }
};

const clearLog = () => {
    fs.writeFileSync(LOG_FILE, '', 'utf-8');
};

module.exports = { log, clearLog };
