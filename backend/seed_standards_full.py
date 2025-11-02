"""
ISO 17662:2016 standardının tüm şablonlarını JSON'dan yükle
"""
import asyncio
import json
from pathlib import Path
from database import AsyncSessionLocal
from standards_models import CalibrasyonStandardi, StandardSablon, SablonParametre


async def load_iso_17662_from_json():
    """JSON dosyasından ISO 17662:2016 standardını yükle"""
    
    # JSON'u oku
    json_path = Path("../Zz-iso-17020-662.md")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    iso_data = data['ISO_17662_2016']
    
    async with AsyncSessionLocal() as db:
        # 1. Standart oluştur
        standart_info = iso_data['standard_info']
        env_cond = iso_data['environmental_conditions']
        
        standart = CalibrasyonStandardi(
            kod=standart_info['code'],
            ad_en=standart_info['name_en'],
            ad_tr=standart_info['name_tr'],
            organizasyon=standart_info['organization'],
            yil=standart_info['year'],
            aciklama=f"{standart_info['edition']} - Kaynak ekipmanları için kalibrasyon standardı",
            varsayilan_kalibrasyon_suresi_ay=12,
            varsayilan_sicaklik_min=float(env_cond['temperature']['min']),
            varsayilan_sicaklik_max=float(env_cond['temperature']['max']),
            varsayilan_nem_min=float(env_cond['humidity']['min']),
            varsayilan_nem_max=float(env_cond['humidity']['max'])
        )
        db.add(standart)
        await db.flush()
        
        print(f"✅ Standart oluşturuldu: {standart.kod}")
        
        # 2. Tüm şablonları yükle
        templates = iso_data['templates']
        total_params = 0
        
        for template_key, template_data in templates.items():
            # Şablon oluştur
            sablon = StandardSablon(
                standart_id=standart.id,
                cihaz_tipi_kodu=template_key,
                cihaz_tipi_adi=template_data['device_type'],
                grup=template_data['device_group'],
                referans=template_data['reference'],
                kalibrasyon_suresi_ay=template_data['calibration_period_months']
            )
            db.add(sablon)
            await db.flush()
            
            # Parametreleri ekle
            for param in template_data['parameters']:
                db.add(SablonParametre(
                    sablon_id=sablon.id,
                    parametre_adi=param['name'],
                    parametre_kodu=param['parameter_code'],
                    birim=param['unit'],
                    tolerans_tipi=param['tolerance_type'],
                    tolerans_degeri=param['tolerance_value'],
                    test_noktalari=param['test_points'],
                    zorunlu=param.get('required', True),
                    referans=param.get('reference', template_data['reference'])
                ))
                total_params += 1
            
            print(f"   ├─ {template_data['device_type']}: {len(template_data['parameters'])} parametre")
        
        await db.commit()
        
        print(f"\n🎉 ISO 17662:2016 standardı tam olarak yüklendi!")
        print(f"   - Toplam Şablon: {len(templates)}")
        print(f"   - Toplam Parametre: {total_params}")


async def load_euramet_cg18():
    """EURAMET cg-18 Terazi standardını yükle"""
    
    async with AsyncSessionLocal() as db:
        # Standart oluştur
        standart = CalibrasyonStandardi(
            kod="EURAMET cg-18",
            ad_en="Guidelines on the Calibration of Non-Automatic Weighing Instruments",
            ad_tr="Otomatik Olmayan Tartı Aletlerinin Kalibrasyonu Kılavuzu",
            organizasyon="EURAMET",
            yil=2015,
            aciklama="Terazi ve hassas tartı aletleri için kalibrasyon kılavuzu"
        )
        db.add(standart)
        await db.flush()
        
        # Terazi şablonu
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
        
        # Parametreler
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
                "test_noktalari": [5000],
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
        print(f"\n✅ EURAMET cg-18 standardı yüklendi!")
        print(f"   - Terazi: 3 parametre")


async def main():
    """Tüm standartları yükle"""
    print("🔧 KALIBRASYON STANDARTLARI YÜKLENİYOR")
    print("=" * 60)
    print()
    
    # Önce mevcut standartları temizle (opsiyonel)
    # await db.execute("TRUNCATE TABLE sablon_parametreleri, standard_sablonlari, kalibrasyon_standartlari CASCADE;")
    
    await load_iso_17662_from_json()
    # EURAMET kaldırıldı - sadece ISO 17662 kullanılıyor
    # await load_euramet_cg18()
    
    print()
    print("=" * 60)
    print("✅ TÜM STANDARTLAR BAŞARIYLA YÜKLENDİ!")
    print()
    print("Yüklenen Standartlar:")
    print("  1. ISO 17662:2016 - 6 cihaz tipi, 23+ parametre")
    print("  2. EURAMET cg-18 - 1 cihaz tipi, 3 parametre")


if __name__ == "__main__":
    asyncio.run(main())
