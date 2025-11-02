import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# 1. Organizasyon oluştur
print("1. Organizasyon oluşturuluyor...")
org_data = {
    "ad": "Test Organizasyon - Kasım 2024",
    "musteri_adi": "Test Müşteri A.Ş.",
    "musteri_adres": "Test Sokak No:123 İstanbul",
    "notlar": "Test amaçlı organizasyon",
    "created_by": "test_user"
}

response = requests.post(f"{BASE_URL}/api/organizasyonlar", json=org_data)
if response.status_code == 200:
    org = response.json()
    print(f"✅ Organizasyon oluşturuldu! ID: {org['id']}")
    org_id = org['id']
else:
    print(f"❌ Hata: {response.status_code} - {response.text}")
    org_id = 1

# 2. Cihaz oluştur
print("\n2. Cihaz oluşturuluyor...")
cihaz_data = {
    "cihaz_kodu": "DK-001",
    "cihaz_adi": "Dijital Kumpas",
    "cihaz_tipi": "kumpas",
    "marka": "Mitutoyo",
    "model": "CD-15CPX",
    "seri_no": "123456",
    "olcme_araligi": "0-150 mm",
    "cozunurluk": "0.01 mm"
}

response = requests.post(f"{BASE_URL}/api/cihazlar", json=cihaz_data)
if response.status_code == 200:
    cihaz = response.json()
    print(f"✅ Cihaz oluşturuldu! ID: {cihaz['id']}")
    cihaz_id = cihaz['id']
else:
    print(f"❌ Hata: {response.status_code} - {response.text}")
    cihaz_id = 1

# 3. Organizasyonları listele
print("\n3. Organizasyonlar listeleniyor...")
response = requests.get(f"{BASE_URL}/api/organizasyonlar")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Toplam {len(data['organizasyonlar'])} organizasyon bulundu:")
    for org in data['organizasyonlar']:
        print(f"   - {org['ad']} ({org['durum']})")
else:
    print(f"❌ Hata: {response.status_code} - {response.text}")

# 4. Cihazları listele
print("\n4. Cihazlar listeleniyor...")
response = requests.get(f"{BASE_URL}/api/cihazlar")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Toplam {len(data['cihazlar'])} cihaz bulundu:")
    for cihaz in data['cihazlar']:
        print(f"   - {cihaz['kod']} - {cihaz['ad']}")
else:
    print(f"❌ Hata: {response.status_code} - {response.text}")

print(f"\n📝 Flutter'da kullanmak için:")
print(f"   - Organizasyon ID: {org_id}")
print(f"   - Cihaz ID: {cihaz_id}")
