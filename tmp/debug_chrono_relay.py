from curl_cffi import requests
import json
import time

def test_chrono_geocode(zipcode="75001", city="PARIS", country="FR"):
    url = "https://www.chronopost.fr/expeditionAvanceeSec/stubgeocodepoint.json"
    
    params = {
        "z": zipcode,
        "c": city,
        "p": country,
        "_": int(time.time() * 1000)
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.chronopost.fr/"
    }

    try:
        r = requests.get(url, params=params, headers=headers, impersonate="chrome120")
        if r.status_code == 200:
            print(f"Geocode Success for {zipcode} {city} {country}")
            print(json.dumps(r.json(), indent=2))
        else:
            print(f"Geocode Failed ({r.status_code})")
    except Exception as e:
        print(f"Geocode Exception: {str(e)}")

if __name__ == "__main__":
    test_chrono_geocode("75001", "PARIS", "FR")
    test_chrono_geocode("1000", "BRUXELLES", "BE")
    test_chrono_geocode("10115", "BERLIN", "DE")
