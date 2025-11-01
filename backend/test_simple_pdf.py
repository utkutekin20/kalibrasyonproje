import requests
import json

# Basit test verisi
data = {
    "muayene_turu": "Test Muayenesi",
    "tarih": "01.11.2025",
    "teknisyen": "Test Teknisyen",
    "cihaz_bilgileri": {
        "marka": "Test Marka",
        "model": "Test Model",
        "seri_no": "12345"
    },
    "olcum_sonuclari": {
        "Sicaklik": "25C",
        "Basinc": "1 bar"
    },
    "notlar": "Test notlari"
}

# Basit PDF endpoint'ini test et
response = requests.post(
    'http://localhost:8000/api/create-pdf',
    json=data,
    headers={'Content-Type': 'application/json'}
)

if response.status_code == 200:
    with open('test_simple_output.pdf', 'wb') as f:
        f.write(response.content)
    print("OK - Basit PDF basariyla olusturuldu!")
else:
    print(f"HATA: {response.status_code}")
    print(response.text)

