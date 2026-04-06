const path = require('path');
const fs = require('fs');

const SCRIPT_DIR = __dirname;
const LOGS_DIR = path.join(SCRIPT_DIR, 'logs');
const OUTPUT_DIR = path.join(SCRIPT_DIR, 'output');

[LOGS_DIR, OUTPUT_DIR].forEach(d => {
    if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
});

module.exports = {
    IS_SERVER:      true,
    HEADLESS:       true,
    VIEWPORT:       { width: 1920, height: 1080 },

    LOG_FILE:       path.join(LOGS_DIR, 'automation.log'),
    TOKEN_FILE:     path.join(OUTPUT_DIR, 'bearer_token.txt'),
    MAIL_LOG:       path.join(LOGS_DIR, 'mails_recus.txt'),

    EMAIL:   "antoineprogsh@gmail.com",
    PASS:    "Lolman349!?",

    IMAP: {
        user:     "antoineprogsh@gmail.com",
        password: "aszflvfzaqfpxjqi",
        host:     "imap.gmail.com",
        port:     993,
        tls:      true,
        tlsOptions: { rejectUnauthorized: false },
        authTimeout: 5000
    },

    USER_AGENT: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",

    SELECTORS: {
        COOKIE_OK:     'text="OK pour moi"',
        COOKIE_OVERLAY:'axeptio_overlay',
        LOGIN_BTN:     'xpath=/html/body/div[2]/main/div/div[1]/div/form/button',
        EMAIL_INPUT:   'xpath=/html/body/div[1]/div[2]/form/div[1]/input',
        PASS_INPUT:    'xpath=/html/body/div[1]/div[2]/form/div[2]/input',
        SUBMIT_BTN:    'xpath=/html/body/div[1]/div[2]/form/div[6]/button',
        A2F_INPUT:     'xpath=/html/body/div/div[2]/form/div[1]/input',
        A2F_SUBMIT:    'xpath=/html/body/div/div[2]/form/div[2]/button',
        SAVE_BTN:      'xpath=/html/body/div[2]/div/div[1]/form/button[1]/div'
    },

    URLS: {
        LOGIN:   'https://www.flunch.fr/fidelite/connexion',
        PROFILE: 'https://www.flunch.fr/fidelite/mon-profil'
    },

    COLORS: {
        RESET:   "\x1b[0m", BOLD: "\x1b[1m", GREY: "\x1b[90m",
        BLUE:    "\x1b[34m", CYAN: "\x1b[36m", GREEN: "\x1b[32m",
        YELLOW:  "\x1b[33m", RED: "\x1b[31m", MAGENTA: "\x1b[35m"
    }
};
