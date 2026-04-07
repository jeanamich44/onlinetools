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
    MAIL_LOG:       path.join(OUTPUT_DIR, 'mails_recus.txt'),
    SCREENSHOT:     path.join(OUTPUT_DIR, 'screenshot.png'),

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
        LOGIN_BTN:     'xpath=/html/body/div[2]/main/div/div[1]/div/form/button',
        EMAIL_INPUT:   'xpath=/html/body/div[1]/div[2]/form/div[1]/input',
        PASS_INPUT:    'xpath=/html/body/div[1]/div[2]/form/div[2]/input',
        SUBMIT_BTN:    'xpath=/html/body/div[1]/div[2]/form/div[6]/button',
        A2F_INPUT:     'xpath=/html/body/div/div[2]/form/div[1]/input',
        A2F_SUBMIT:    'xpath=/html/body/div/div[2]/form/div[2]/button',
        PROFILE_ACTION_BTN: 'xpath=/html/body/div[2]/div/div[1]/form/button[1]/div'
    },

    URLS: {
        IP_TEST: 'https://ip.decodo.com/json',
        LOGIN:   'https://www.flunch.fr/fidelite/connexion',
        PROFILE: 'https://www.flunch.fr/fidelite/mon-profil'
    },

    // Délais utilisés à chaque étape du script principal (en millisecondes)
    DELAYS: {
        POST_IP_TEST:           2000,  // [0] Après la visite de l'IP proxy
        POST_HOMEPAGE:          2000,  // [1] Après chargement de l'accueil Flunch (attente popup cookies)
        POST_COOKIE:            2000,  // [3] Après clic sur "OK pour moi" (cookies)
        POST_LOGIN_FORM_OPEN:   5000,  // [5] Après clic pour ouvrir le formulaire (attente chargement iframe/form)
        POST_EMAIL_INPUT:       3000,  // [7] Entre la saisie de l'email et du mot de passe
        POST_SUBMIT_LOGIN:      3000,  // [10] Après le clic sur "Se connecter", attente d'apparition de la page A2F
        IMAP_RETRY:             4000,  // [12] Délai d'attente entre deux vérifications de boite mail
        POST_A2F_SUBMIT:        5000,  // [14] Après saisie du code A2F et clic sur valider
        POST_PROFILE_NAV:       5000,  // [17] Délai de chargement de la page Mon Profil
        POST_PROFILE_ACTION:    1000   // [18] Délai final après le clic sur le mouton ciblé dans le profil
    },

    COLORS: {
        RESET: "\x1b[0m", MAGENTA: "\x1b[35m", CYAN: "\x1b[36m", 
        YELLOW: "\x1b[33m", GREEN: "\x1b[32m", RED: "\x1b[31m", GREY: "\x1b[90m"
    },

    // INFOS PROXIES RESIDENTIELS DECODO
    PROXIES: [
        {
            server:   "http://gate.decodo.com:10001",
            username: "user-sppp614s0d-asn-3215",
            password: "3vc9xbnLP9+D0dbTho"
        },
        {
            server:   "http://gate.decodo.com:10002",
            username: "user-sppp614s0d-asn-3215",
            password: "3vc9xbnLP9+D0dbTho"
        },
        {
            server:   "http://gate.decodo.com:10003",
            username: "user-sppp614s0d-asn-3215",
            password: "3vc9xbnLP9+D0dbTho"
        }
    ]
};
