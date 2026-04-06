let capturedToken = null;

const getToken = () => capturedToken;

const setupInterceptors = (page) => {
    page.on('request', req => {
        if (req.url().includes('update_client_data')) {
            const h = req.headers();
            if (h['authorization']) {
                capturedToken = h['authorization'].startsWith('Bearer ') ? h['authorization'].substring(7) : h['authorization'];
            }
        }
    });
};

module.exports = { setupInterceptors, getToken };
