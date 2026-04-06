const imaps = require('imap-simple');
const { simpleParser } = require('mailparser');
const fs = require('fs');
const { IMAP, MAIL_LOG, COLORS } = require('./config');
const { log } = require('./logger');

const fetchLastCodeAndDelete = async () => {
    log("Recherche email A2F...", "A2F", COLORS.MAGENTA);
    try {
        const connection = await imaps.connect({ imap: IMAP });
        await connection.openBox('INBOX');
        const messages = await connection.search(['ALL'], { bodies: [''], struct: true, markSeen: false });
        const lastMessages = messages.slice(-15).reverse();
        let codeFound = null;

        for (const msg of lastMessages) {
            const allPart = msg.parts.find(p => p.which === '');
            const mail = await simpleParser(allPart.body);
            const fromStr = mail.from ? mail.from.text : "";
            const bodyStr = (mail.text || (mail.html ? mail.html.replace(/<[^>]*>?/gm, ' ') : "")).replace(/\s+/g, ' ');

            if (fromStr.toLowerCase().includes('flunch')) {
                const match = bodyStr.match(/\b\d{6}\b/);
                if (match) {
                    codeFound = match[0];
                    const now = new Date().toLocaleString('fr-FR');
                    const mailEntry = `\n────────────────────────────\n  SESSION : ${now}\n  CODE    : ${codeFound}\n────────────────────────────\n`;
                    fs.appendFileSync(MAIL_LOG, mailEntry, 'utf8');
                    await connection.addFlags(msg.attributes.uid, '\\Deleted');
                    break;
                }
            }
        }
        await connection.imap.expunge();
        connection.end();
        return codeFound;
    } catch (err) {
        log(`Erreur IMAP: ${err.message}`, "A2F", COLORS.RED);
        return null;
    }
};

module.exports = { fetchLastCodeAndDelete };
