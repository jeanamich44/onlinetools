const fs = require('fs');
const { LOG_FILE } = require('./config');

const init = () => {
    fs.appendFileSync(LOG_FILE, `\n--- NOUVELLE SESSION : ${new Date().toLocaleString()} ---\n`);
};

const log = (msg, category, color = "") => {
    const entry = `[${category}] ${msg}`;
    console.log(entry);
    fs.appendFileSync(LOG_FILE, `[${new Date().toISOString()}] ${entry}\n`);
};

module.exports = { init, log };
