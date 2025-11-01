"""
Veritabanı API endpoint'lerini test et
"""
import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

# Test verisi - KalibrasyonSertifikasiData formatında
test_data = {
    "sertifikaNo": f"KAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    "genelBilgiler": {
        "musteriAdi": "Test Müşteri A.Ş.",
        "musteriAdres": "Test Sokak No:123 İstanbul",
        "istekNo": "TEST-2024-001"
    },
    "cihazBilgileri": {
        "cihazAdi": "Test Kumpas",
        "marka": "Test Marka",
        "model": "TM-2024",
        "seriNo": "TEST123456",
        "olcmeAraligi": "0-150 mm",
        "cozunurluk": "0.01 mm"
    },
    "kalibrasyonBilgileri": {
        "kalibrasyonTarihi": datetime.now().strftime("%d.%m.%Y"),
        "ortamKosullari": {
            "sicaklik": "23 ± 0.5 °C",
            "nem": "45 ± 5 % RH"
        },
        "referansCihazlar": []
    },
    "olcumSonuclari": {
        "disCapOlcumleri": [
            {
                "tip": "dis",
                "referansDeger": 25.00,
                "olculenDeger": 25.01,
                "sapma": 0.01,
                "belirsizlik": 0.005
            }
        ],
        "icCapOlcumleri": [
            {
                "tip": "ic",
                "referansDeger": 50.00,
                "olculenDeger": 50.02,
                "sapma": 0.02,
                "belirsizlik": 0.008
            }
        ],
        "derinlikOlcumleri": [],
        "kademeOlcumleri": [],
        "paralellikOlcumleri": []
    },
    "uygunlukDegerlendirmesi": {
        "sonuc": True,
        "aciklama": "Cihaz kalibrasyon toleransları içinde uygun bulunmuştur."
    },
    "kalibrasyonuYapanlar": [
        {
            "adSoyad": "Test Teknisyen",
            "unvan": "Kalibrasyon Teknisyeni"
        }
    ],
    "onaylayanlar": [
        {
            "adSoyad": "Test Müdür",
            "unvan": "Teknik Müdür"
        }
    ],
    "laboratuvarBilgileri": {
        "adresi": "Test Laboratuvar Adresi",
        "iletisim": "test@lab.com",
        "akreditasyonBilgisi": "TEST-LAB-001"
    },
    "notlar": []
}


def test_save_report():
    """Rapor kaydetme testi"""
    print("1. Rapor Kaydetme Testi")
    print("-" * 50)
    
    # Direkt veriyi gönder
    response = requests.post(
        f"{BASE_URL}/api/save-report",
        json=test_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Rapor başarıyla kaydedildi!")
        print(f"   - Rapor ID: {result['rapor_id']}")
        print(f"   - Sertifika No: {result['sertifika_no']}")
        print(f"   - PDF: {result['pdf_path']}")
        return result['rapor_id']
    else:
        print(f"❌ Hata: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_list_reports():
    """Raporları listeleme testi"""
    print("\n2. Raporları Listeleme Testi")
    print("-" * 50)
    
    response = requests.get(f"{BASE_URL}/api/reports")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Toplam {result['total']} rapor bulundu")
        
        for i, report in enumerate(result['reports'][:3], 1):
            print(f"\n   {i}. Rapor:")
            print(f"      - ID: {report['id']}")
            print(f"      - Sertifika: {report['sertifika_no']}")
            print(f"      - Müşteri: {report['musteri_adi']}")
            print(f"      - Tarih: {report['kalibrasyon_tarihi']}")
            print(f"      - Uygunluk: {'✓' if report['uygunluk'] else '✗'}")
    else:
        print(f"❌ Hata: {response.status_code}")
        print(f"   {response.text}")


def test_get_report_detail(report_id):
    """Rapor detayı testi"""
    print(f"\n3. Rapor Detayı Testi (ID: {report_id})")
    print("-" * 50)
    
    response = requests.get(f"{BASE_URL}/api/reports/{report_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Rapor detayları:")
        print(f"   - Sertifika: {result['rapor']['sertifika_no']}")
        print(f"   - Ölçüm Sayısı: {len(result['olcumler'])}")
        print(f"   - PDF: {result['rapor']['pdf_path']}")
    else:
        print(f"❌ Hata: {response.status_code}")
        print(f"   {response.text}")


if __name__ == "__main__":
    print("\n🔧 VERİTABANI API TESTLERİ\n")
    
    # 1. Rapor kaydet
    new_report_id = test_save_report()
    
    # 2. Raporları listele
    test_list_reports()
    
    # 3. Rapor detayını getir
    if new_report_id:
        test_get_report_detail(new_report_id)
    
    print("\n✅ Testler tamamlandı!")
