let capturedToken = null;
const { log } = require('./logger');

const getToken = () => capturedToken;

const setupInterceptors = (page) => {
    page.on('request', req => {
        const url = req.url();
        const headers = req.headers();
        const method = req.method();

        // 1. On log TOUTES les requêtes réseau pour debugging
        // On tronque ce qui n'est pas Flunch ou trop long (images, styles)
        if (url.includes('flunch.fr') && !url.match(/\.(png|jpg|css|woff2|svg)$/)) {
            log(`[${method}] URL: ${url.substring(0, 80)}...`, "TRACE", "#808080");
        }

        // 2. On cherche précisément le Token
        if (headers['authorization']) {
            const auth = headers['authorization'];
            const token = auth.startsWith('Bearer ') ? auth.substring(7).trim() : auth.trim();
            const len = token.length;
            
            if (token.startsWith('ey') && len >= 730 && len <= 780) {
                log(`TOKEN CAPTURÉ VALIDE (LEN: ${len}) [${url.substring(0, 30)}...]`, "NETWORK", "#32CD32");
                capturedToken = token;
            } else {
                const reason = !token.startsWith('ey') ? "pas ey..." : `LEN incorrecte (${len})`;
                log(`TOKEN REJETÉ [${reason}] sur ${url.substring(0, 30)}...`, "DEBUG", "#FF8C00");
            }
        }
    });

    // 3. Log des erreurs réseau (si le site est bloqué par Railway)
    page.on('requestfailed', req => {
        log(`Échec réseau : ${req.url().substring(0, 40)} - ${req.failure().errorText}`, "NETFAIL", "#FF0000");
    });
};

module.exports = { setupInterceptors, getToken };
