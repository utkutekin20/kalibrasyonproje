import requests
import json

# Test dosyasını oku
with open('test_kalibrasyon.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# API'ye gönder
response = requests.post(
    'http://localhost:8000/api/create-kalibrasyon-pdf',
    json=data,
    headers={'Content-Type': 'application/json'}
)

if response.status_code == 200:
    # PDF'i kaydet
    with open('test_output.pdf', 'wb') as f:
        f.write(response.content)
    print("OK - PDF basariyla olusturuldu: test_output.pdf")
else:
    print(f"HATA: {response.status_code}")
    print(response.text)

