let capturedToken = null;

const getToken = () => capturedToken;

const setupInterceptors = (page) => {
    // On écoute TOUTES les requêtes sortantes
    page.on('request', req => {
        const url = req.url();
        const headers = req.headers();
        
        // Si la requête va vers l'API de Flunch et possède un header Authorization
        if (url.includes('flunch.fr') && headers['authorization']) {
            const auth = headers['authorization'];
            // On extrait le token du format "Bearer eY..."
            const token = auth.startsWith('Bearer ') ? auth.substring(7).trim() : auth.trim();
            
            // On vérifie que le token commence par ey et fait entre 730 et 780 caractères.
            if (token.startsWith('ey') && token.length >= 730 && token.length <= 780) {
                capturedToken = token;
            }
        }
    });
};

module.exports = { setupInterceptors, getToken };
