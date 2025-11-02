import requests

response = requests.get('http://localhost:8000/api/reports')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nToplam Rapor: {data['total']}")
    print("\nRaporlar:")
    for r in data['reports']:
        print(f"  - ID: {r['id']}, Sertifika: {r['sertifika_no']}, Müşteri: {r['musteri_adi']}")
else:
    print(f"Hata: {response.text}")

