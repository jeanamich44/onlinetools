let capturedToken = null;

const getToken = () => capturedToken;

const { log } = require('./logger');

const setupInterceptors = (page) => {
    page.on('request', req => {
        const url = req.url();
        const headers = req.headers();
        
        if (headers['authorization']) {
            const auth = headers['authorization'];
            const token = auth.startsWith('Bearer ') ? auth.substring(7).trim() : auth.trim();
            const len = token.length;
            const start = token.substring(0, 10);
            
            // On log TOUT pour le debug (ignorer ou valider)
            if (token.startsWith('ey') && len >= 730 && len <= 780) {
                log(`TOKEN VALIDE capture [URL: ${url.substring(0, 40)}...] (LEN: ${len})`, "NETWORK", "#32CD32");
                capturedToken = token;
            } else {
                // On log pourquoi on l'ignore
                const reason = !token.startsWith('ey') ? "pas de prefix ey" : `longueur incorrecte (${len})`;
                log(`TOKEN IGNORE [${reason}] - ${url.substring(0, 40)}...`, "DEBUG", "#808080");
            }
        }
    });
};

module.exports = { setupInterceptors, getToken };
