import requests

print("Testing standart API'leri...")
print()

# 1. Tüm standartları listele
r = requests.get('http://localhost:8000/api/standards')
if r.status_code == 200:
    data = r.json()
    print(f"✅ Toplam {len(data['standartlar'])} standart yüklendi:")
    for s in data['standartlar']:
        print(f"  - {s['kod']} ({s['sablon_sayisi']} şablon)")
else:
    print(f"❌ Hata: {r.status_code}")

print()

# 2. MIG/MAG için standartları getir
r = requests.get('http://localhost:8000/api/standards/mig_mag_welding')
if r.status_code == 200:
    data = r.json()
    print(f"✅ MIG/MAG için {len(data['standartlar'])} standart bulundu")
else:
    print(f"❌ Hata: {r.status_code}")

print()

# 3. Template parametrelerini getir (Şablon ID: 1)
r = requests.get('http://localhost:8000/api/templates/1/parameters')
if r.status_code == 200:
    data = r.json()
    print(f"✅ Şablon #1 için {len(data['parametreler'])} parametre:")
    for p in data['parametreler']:
        print(f"  - {p['ad']}: {p['test_noktalari']} ({p['birim']}, ±{p['tolerans_degeri']}%)")
else:
    print(f"❌ Hata: {r.status_code}")
