"""
Kalibrasyon standartlarını veritabanına yükle
"""
import asyncio
import json
from database import AsyncSessionLocal
from standards_models import CalibrasyonStandardi, StandardSablon, SablonParametre


async def seed_iso_17662():
    """ISO 17662:2016 standardını ve şablonlarını yükle"""
    
    async with AsyncSessionLocal() as db:
        # 1. Standart oluştur
        standart = CalibrasyonStandardi(
            kod="ISO 17662:2016",
            ad_en="Welding - Calibration, verification and validation of equipment",
            ad_tr="Kaynak - Kaynak ekipmanlarının kalibrasyonu, doğrulanması ve validasyonu",
            organizasyon="ISO",
            yil=2016,
            aciklama="Kaynak ekipmanları için kalibrasyon standardı",
            varsayilan_kalibrasyon_suresi_ay=12,
            varsayilan_sicaklik_min=18.0,
            varsayilan_sicaklik_max=28.0,
            varsayilan_nem_min=30.0,
            varsayilan_nem_max=70.0
        )
        db.add(standart)
        await db.flush()
        
        # 2. MIG/MAG Kaynak Şablonu
        mig_mag = StandardSablon(
            standart_id=standart.id,
            cihaz_tipi_kodu="mig_mag_welding",
            cihaz_tipi_adi="MIG/MAG Kaynak Makinesi",
            grup="Group 1 - Arc Welding",
            referans="Madde 5.3, Tablo 9-12",
            kalibrasyon_suresi_ay=12
        )
        db.add(mig_mag)
        await db.flush()
        
        # MIG/MAG Parametreleri
        parametreler = [
            {
                "parametre_adi": "Kaynak Akımı",
                "parametre_kodu": "welding_current",
                "birim": "A",
                "tolerans_tipi": "percentage",
                "tolerans_degeri": 2.0,
                "test_noktalari": [50, 100, 150, 200, 250, 300],
                "zorunlu": True,
                "referans": "Madde 5.3"
            },
            {
                "parametre_adi": "Ark Gerilimi",
                "parametre_kodu": "arc_voltage",
                "birim": "V",
                "tolerans_tipi": "percentage",
                "tolerans_degeri": 2.0,
                "test_noktalari": [15, 20, 25, 30, 35],
                "zorunlu": True,
                "referans": "Madde 5.3"
            },
            {
                "parametre_adi": "Tel Sürme Hızı",
                "parametre_kodu": "wire_feed_speed",
                "birim": "m/min",
                "tolerans_tipi": "percentage",
                "tolerans_degeri": 5.0,
                "test_noktalari": [2, 4, 6, 8, 10, 12],
                "zorunlu": True,
                "referans": "Madde 5.3"
            },
            {
                "parametre_adi": "Koruyucu Gaz Akışı",
                "parametre_kodu": "shielding_gas_flow",
                "birim": "L/min",
                "tolerans_tipi": "percentage",
                "tolerans_degeri": 20.0,
                "test_noktalari": [10, 15, 20, 25],
                "zorunlu": True,
                "referans": "Tablo 8"
            }
        ]
        
        for param in parametreler:
            db.add(SablonParametre(
                sablon_id=mig_mag.id,
                **param
            ))
        
        # 3. TIG Kaynak Şablonu
        tig = StandardSablon(
            standart_id=standart.id,
            cihaz_tipi_kodu="tig_welding",
            cihaz_tipi_adi="TIG Kaynak Makinesi",
            grup="Group 1 - Arc Welding",
            referans="Madde 5.3",
            kalibrasyon_suresi_ay=12
        )
        db.add(tig)
        await db.flush()
        
        tig_parametreleri = [
            {
                "parametre_adi": "Kaynak Akımı",
                "parametre_kodu": "welding_current",
                "birim": "A",
                "tolerans_tipi": "percentage",
                "tolerans_degeri": 2.0,
                "test_noktalari": [20, 50, 100, 150, 200],
                "zorunlu": True,
                "referans": "Madde 5.3"
            },
            {
                "parametre_adi": "Ark Gerilimi",
                "parametre_kodu": "arc_voltage",
                "birim": "V",
                "tolerans_tipi": "percentage",
                "tolerans_degeri": 2.0,
                "test_noktalari": [10, 15, 20, 25],
                "zorunlu": True,
                "referans": "Madde 5.3"
            },
            {
                "parametre_adi": "Koruyucu Gaz Akışı",
                "parametre_kodu": "shielding_gas_flow",
                "birim": "L/min",
                "tolerans_tipi": "percentage",
                "tolerans_degeri": 20.0,
                "test_noktalari": [5, 10, 15, 20],
                "zorunlu": True,
                "referans": "Madde 5.3"
            }
        ]
        
        for param in tig_parametreleri:
            db.add(SablonParametre(
                sablon_id=tig.id,
                **param
            ))
        
        await db.commit()
        print("✅ ISO 17662:2016 standardı başarıyla yüklendi!")
        print(f"   - MIG/MAG: {len(parametreler)} parametre")
        print(f"   - TIG: {len(tig_parametreleri)} parametre")


async def seed_euramet_cg18():
    """EURAMET cg-18 (Terazi kalibrasyonu) standardını yükle"""
    
    async with AsyncSessionLocal() as db:
        # 1. Standart oluştur
        standart = CalibrasyonStandardi(
            kod="EURAMET cg-18",
            ad_en="Guidelines on the Calibration of Non-Automatic Weighing Instruments",
            ad_tr="Otomatik Olmayan Tartı Aletlerinin Kalibrasyonu Kılavuzu",
            organizasyon="EURAMET",
            yil=2015,
            aciklama="Terazi ve hassas tartı aletleri için kalibrasyon kılavuzu",
            varsayilan_kalibrasyon_suresi_ay=12
        )
        db.add(standart)
        await db.flush()
        
        # 2. Terazi Şablonu
        terazi = StandardSablon(
            standart_id=standart.id,
            cihaz_tipi_kodu="terazi",
            cihaz_tipi_adi="Hassas Terazi",
            grup="Non-Automatic Weighing Instruments",
            referans="EURAMET cg-18",
            kalibrasyon_suresi_ay=12
        )
        db.add(terazi)
        await db.flush()
        
        # Terazi parametreleri
        parametreler = [
            {
                "parametre_adi": "Tekrarlanabilirlik",
                "parametre_kodu": "repeatability",
                "birim": "g",
                "tolerans_tipi": "absolute",
                "tolerans_degeri": 0.01,
                "test_noktalari": [100, 500, 1000, 5000, 10000],
                "zorunlu": True,
                "referans": "Section 4.1"
            },
            {
                "parametre_adi": "Doğrusallık",
                "parametre_kodu": "linearity",
                "birim": "g",
                "tolerans_tipi": "percentage",
                "tolerans_degeri": 0.1,
                "test_noktalari": [0, 2500, 5000, 7500, 10000],
                "zorunlu": True,
                "referans": "Section 4.2"
            },
            {
                "parametre_adi": "Köşe Yükleme Testi",
                "parametre_kodu": "eccentricity",
                "birim": "g",
                "tolerans_tipi": "absolute",
                "tolerans_degeri": 0.02,
                "test_noktalari": [5000],  # Merkez, 4 köşe
                "zorunlu": True,
                "referans": "Section 4.3"
            }
        ]
        
        for param in parametreler:
            db.add(SablonParametre(
                sablon_id=terazi.id,
                **param
            ))
        
        await db.commit()
        print("✅ EURAMET cg-18 standardı başarıyla yüklendi!")


async def main():
    """Tüm standartları yükle"""
    print("🔧 Kalibrasyon standartları veritabanına yükleniyor...")
    print()
    
    await seed_iso_17662()
    print()
    await seed_euramet_cg18()
    print()
    print("🎉 Tüm standartlar başarıyla yüklendi!")


if __name__ == "__main__":
    asyncio.run(main())
