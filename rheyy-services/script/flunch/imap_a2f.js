const imaps = require('imap-simple');
const { simpleParser } = require('mailparser');
const fs = require('fs');
const { IMAP, MAIL_LOG, COLORS } = require('./config');
const { log } = require('./logger');

const fetchLastCodeAndDelete = async () => {
    log("Recherche email A2F...", "A2F", COLORS.CYAN);
    try {
        const connection = await imaps.connect({ imap: IMAP });
        await connection.openBox('INBOX');
        
        const messages = await connection.search(['ALL'], { bodies: [''], struct: true, markSeen: false });
        const lastMessages = messages.slice(-10).reverse();
        let codeFound = null;

        for (const msg of lastMessages) {
            const allPart = msg.parts.find(p => p.which === '');
            const mail = await simpleParser(allPart.body);
            
            const fromStr = mail.from ? mail.from.text : "";
            const subject = mail.subject || "";
            const bodyStr = (mail.text || "") + " " + (mail.html || "");

            log(`Examen mail de: ${fromStr} | Sujet: ${subject}`, "TRACE", COLORS.GREY);

            if (fromStr.toLowerCase().includes('flunch') || subject.toLowerCase().includes('flunch')) {
                log("Mail Flunch détecté ! Analyse du contenu...", "TRACE", COLORS.YELLOW);
                
                // Nettoyage complet du style et des balises HTML pour éviter les faux positifs (comme #333333)
                const cleanText = bodyStr.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, ' ')
                                         .replace(/<[^>]*>?/gm, ' ')
                                         .replace(/&[a-z0-9]+;/gi, ' ');

                // On cherche ensuite la séquence de 6 chiffres dans le texte brut
                const match = cleanText.match(/\b\d{6}\b/);
                if (match) {
                    codeFound = match[0];
                    log(`CODE TROUVÉ: ${codeFound}`, "A2F", COLORS.GREEN);
                    fs.appendFileSync(MAIL_LOG, `[${new Date().toLocaleString()}] CODE : ${codeFound}\n`);
                    await connection.addFlags(msg.attributes.uid, '\\Deleted');
                    break;
                } else {
                    log("Aucun code à 6 chiffres trouvé dans ce mail.", "TRACE", COLORS.GREY);
                    log(`Extrait du texte lu: ${cleanText.substring(0, 500).trim()}...`, "TRACE", COLORS.GREY);
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
