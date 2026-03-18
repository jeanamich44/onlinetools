from .p_utils import get_current_cart_date, iv4, USER_AGENT

HEADERS_1 = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "cookie": (
        "JSESSIONID_TEMCHRONOWEB=8B80008D2969D9C0C1F7EA11F2DDFC24.te-mchronowebi2-NODE14; "
        "iv4=f339aa20b62de67c9adcc8fc99b8e619; "
        "parcours=Professionnel; "
        "parcoursId=4"
    ),
    "priority": "u=0, i",
    "referer": "https://www.chronopost.fr/fr",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
}



HEADERS_4 = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "referer": "https://www.chronopost.fr/expedier/accueilShipping.do?reinit=true&lang=fr_FR",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "cookie": (
        "W0827094_40859_87668902=17; "
        "W1410789_3100_25322901=17; "
        "W2791128_24938_52070101=17; "
        "W2782179_21811_17617101=1; "
        "W2782179_47107_15972103=86; "
        "W1029613_47107_15972103=1; "
        "W1029613__=1; "
        "W2919011_47107_15972103=1; "
        "CookieConsent={stamp:%27wtKkoH0MD5wMffkNpelOoPcweUhXzVkPLiTsGBi9NqOS87rdsbpILA==%27%2Cnecessary:true%2Cpreferences:true%2Cstatistics:true%2Cmarketing:true%2Cmethod:%27explicit%27%2Cver:1%2Cutc:1772309488825%2Cregion:%27fr%27}; "
        "iv4=f339aa20b62de67c9adcc8fc99b8e619; "
        "cookie_profile_role=4; "
        "WebProRef=W2919011; "
        "_gcl_au=1.1.1006519497.1772750562; "
        "cookie_nbCartArticles=0; "
        "cookie_ie6=true; "
        "lang=fr_FR; "
        "SAWWID=.tc-mchronoweb-NODE3; "
        "JSESSIONID_WSREST=.tc-mchronoweb-NODE3; "
        "parcours=Professionnel; "
        "parcoursId=4; "
        "cf_clearance=evQCN.fAzzmddARbWc7zrPjd4negqU7xiBqfCbun1AQ-1773843146-1.2.1.1-ZQKF17zPy8_dvi9A6sUfui.oE3cWUA0WfafE8K715.cUlPGOn04LTjFeXTqOl6psGfHa50JAFWKy8.SQw37pOzayCyUpogEgOSJ.VPkc6OGQyudrpttK2KCtkk2LyEn8MmCPR6qRnDovkASETX0QGC5.2MFMEdmzRFLHECCnp2vxNAxkq.Fm8cooHfKjQFKgcmHMY72dtEQSJFI9pkeF8Tb6RYCP_s7O17wRUTSa4OzXea5x8b8tp1jwtxyGptj0kQj19hqCYIxC5.JcrZUDlaeFGpcNweWzON2.V79WuNhRSD3shWhDDk0VQzufSH2FNBoTzfoU_LMUEBBgZWSA0Q; "
        "__cf_bm=_jArMYmBnOIyUvuM9RHc5IvwHqV6wmI.j3P3I0fOI54-1773843146.1570714-1.0.1.1-2YiyzWQHjH6QBpVxr1O76EMSHgdYn5fQZjN6rUQuze_CfNlfKgG1A7Uws1naWlCsCGrSP4D4WwLeaQTPAGfSnwB8o128HDr_7UZOhAZE8nvfQJS3ebD5tkHqyq1lx.o5; "
        "cookie_idSessionShipping=31FC825A800F00AEFC06EDCD181E6BEC.te-mchronowebi2-NODE8; "
        "cookie_idCart=298314560; "
        "cookie_lastCartUpdate=18/03/2026/15:21; "
        "JSESSIONID_WSSHIPPING=8BC01FBA44E1626560695E4AEFEA5887.tc-wsshipping-NODE7"
    ),
}

SIMULATEUR_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "fr-FR,fr;q=0.9",
    "content-type": "application/json",
    "cookie": "lang=fr_FR; JSESSIONID_WSREST=.tc-mchronoweb-NODE7; parcours=Particulier; parcoursId=2;",
    "origin": "https://www.chronopost.fr",
    "priority": "u=1, i",
    "referer": "https://www.chronopost.fr/small-webapp/",
    "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": USER_AGENT
}
