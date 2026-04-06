const fs = require('fs');
const { LOG_FILE, COLORS } = require('./config');
const { log } = require('./logger');

let capturedToken = null;

const getToken = () => capturedToken;

const setupInterceptors = (page) => {
    page.on('request', req => {
        log(`REQ: ${req.method()} ${req.url()}`, "NETWORK", COLORS.GREY, true);

        if (req.url().includes('update_client_data')) {
            const h = req.headers();
            if (h['authorization']) {
                capturedToken = h['authorization'].startsWith('Bearer ') ? h['authorization'].substring(7) : h['authorization'];
                log(`TOKEN CAPTURÉ: ${capturedToken.substring(0, 20)}...`, "TOKEN", COLORS.GREEN);
            }
        }
    });

    page.on('response', async res => {
        log(`RES: ${res.status()} ${res.url()}`, "NETWORK", COLORS.GREY, true);
    });
};

module.exports = { setupInterceptors, getToken };
