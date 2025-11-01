from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import openai
import os
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv
import base64
from fpdf import FPDF
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import asyncio

# production.env dosyasını yükle
env_file = Path(__file__).parent / "production.env"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()  # .env dosyasını dene

app = FastAPI(title="VIDCO AI Co-Pilot Backend")

# CORS ayarları - Development için wildcard, production için spesifik originler
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development: tüm originlere izin ver (Flutter web random port kullanıyor)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Dosya kaydetme dizini
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)


class TranscriptionRequest(BaseModel):
    text: str


class ReportData(BaseModel):
    muayene_turu: str
    tarih: str
    teknisyen: str
    cihaz_bilgileri: dict
    olcum_sonuclari: dict
    notlar: str
    gorsel_analiz: dict = None  # Yeni alan


class KalibrasyonSertifikasiData(BaseModel):
    kalibrasyon_sertifikasi: dict


class ImageAnalysisRequest(BaseModel):
    image_base64: str


@app.get("/")
async def root():
    return {"message": "VIDCO AI Co-Pilot Backend API", "status": "running"}


@app.post("/api/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    """
    Ses dosyasını metne çevirir (OpenAI Whisper kullanarak)
    """
    try:
        # Dosyayı asenkron kaydet
        file_path = UPLOAD_DIR / file.filename
        content = await file.read()
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # OpenAI Whisper çağrısını thread pool'da çalıştır (blocking I/O)
        def transcribe_audio():
            with open(file_path, "rb") as audio_file:
                return openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="tr"
                )
        
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(executor, transcribe_audio)
        
        # Dosyayı asenkron sil
        await asyncio.to_thread(file_path.unlink)
        
        return {"text": transcript.text, "status": "success"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transkripsiyon hatası: {str(e)}")


@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """
    Görsel analizi yapar (OpenAI GPT-4 Vision kullanarak)
    """
    try:
        # Dosyayı oku ve base64'e çevir
        content = await file.read()
        base64_image = base64.b64encode(content).decode('utf-8')
        
        # OpenAI Vision API çağrısını thread pool'da çalıştır
        def analyze_with_vision():
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Sen bir muayene ve kalibrasyon uzmanısın. Cihaz fotoğraflarını analiz edip detaylı raporlar oluşturursun."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Bu cihazı analiz et ve şu bilgileri JSON formatında ver:
{
    "cihaz_turu": "Cihaz türü (basınç ölçer, termometre, vb.)",
    "gorsel_durum": "Cihazın görsel durumu (hasar, aşınma, temizlik)",
    "gosterge_deger": "Eğer göstergede bir değer okunuyorsa, o değer",
    "anomaliler": ["Tespit edilen sorunlar listesi"],
    "oneriler": ["Öneriler listesi"]
}

Sadece geçerli JSON döndür."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(executor, analyze_with_vision)
        
        # JSON parse et
        analysis_text = response.choices[0].message.content
        
        # JSON ayıklama (bazen markdown code block içinde geliyor)
        if "```json" in analysis_text:
            analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
        elif "```" in analysis_text:
            analysis_text = analysis_text.split("```")[1].split("```")[0].strip()
        
        analysis_json = json.loads(analysis_text)
        
        # Görseli asenkron kaydet
        image_filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = UPLOAD_DIR / image_filename
        
        async with aiofiles.open(image_path, "wb") as f:
            await f.write(content)
        
        return {
            "analysis": analysis_json,
            "image_filename": image_filename,
            "image_base64": base64_image,
            "status": "success"
        }
    
    except Exception as e:
        import traceback
        print(f"GORSEL ANALIZ HATA: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Görsel analiz hatası: {str(e)}")


@app.post("/api/generate-report")
async def generate_report(request: TranscriptionRequest):
    """
    Metinden rapor verisi oluşturur (GPT-4o kullanarak)
    """
    try:
        prompt = f"""
Aşağıdaki ses kaydı metninden detaylı bir kalibrasyon sertifikası oluştur.

Metin: {request.text}

Tam bu JSON formatında döndür:
{{
  "kalibrasyon_sertifikasi": {{
    "sertifika_bilgileri": {{
      "firma": "AS KALİBRASYON İÇ VE DIŞ TİCARET SAN. PAZ. LTD.ŞTİ.",
      "adres": "Meriç Mahallesi 5747/10 Sokak No:12/2 Bornova / İZMİR",
      "telefon": "232 247 07 44",
      "faks": "232 431 07 44",
      "email": "satis@askalibrasyon.com",
      "website": "www.askalibrasyon.com",
      "akreditasyon_no": "AB-0068-K",
      "sertifika_no": "KAL-{datetime.now().strftime('%Y%m%d-%H%M')}",
      "tarih": "{datetime.now().strftime('%d.%m.%Y')}"
    }},
    "musteri_bilgileri": {{
      "sahibi": "Ses kaydından çıkar veya 'Test Müşterisi'",
      "adres": "Ses kaydında yoksa 'Belirtilmemiş'",
      "istek_numarasi": "İ-{datetime.now().strftime('%y-%m%d')} / 1"
    }},
    "cihaz_bilgileri": {{
      "makine_cihaz": "Ses kaydından çıkar (örn: KUMPAS, MİKROMETRE)",
      "imalatci": "Ses kaydından çıkar veya '-'",
      "tip": "Ses kaydından çıkar veya '-'",
      "seri_numarasi": "Ses kaydından çıkar veya 'DEMO-001'",
      "kalibrasyon_tarihi": "{datetime.now().strftime('%d.%m.%Y')}",
      "sayfa_sayisi": 2,
      "olcme_araligi": "Ses kaydından çıkar veya '0-150 mm'",
      "cozunurluk": "Ses kaydından çıkar veya '0.01 mm'"
    }},
    "kalibrasyon_detaylari": {{
      "laboratuvara_kabul_tarihi": "{datetime.now().strftime('%d.%m.%Y')}",
      "yontem_prosedur": "Kalibrasyon; MEK.SİT.002 'Kumpas Standart iş talimatı' na uygun olarak yapılmıştır.",
      "cevre_sartlari": {{
        "sicaklik": "20 ± 1°C",
        "bagil_nem": "%45 ± 25 %rh",
        "aciklama": "Kalibrasyon öncesinde test cihazı ve referans cihazlar aynı ortam şartlarında yeterli süre bekletilerek termal dengeye getirilmiştir."
      }}
    }},
    "referans_cihazlar": [
      {{
        "adi": "Granit Pleyt",
        "imalatci": "QUINGDAO",
        "tipi": "-",
        "seri_no": "26087294",
        "izlenebilirlik": "AB-0002-K"
      }},
      {{
        "adi": "Mastar Seti",
        "imalatci": "ACCUD",
        "tipi": "-",
        "seri_no": "160017",
        "izlenebilirlik": "AB-0012-K"
      }}
    ],
    "fonksiyonellik_kontrolu": {{
      "olcme_ceneleri": "Uygun",
      "tespitleme_vidasi": "Uygun",
      "gosterge": "Uygun",
      "tambur_yatak_boslugu": "Uygun",
      "ic_cap_olcme_ceneleri": "Uygun",
      "derinlik_olcme_ceneleri": "Uygun"
    }},
    "olcum_sonuclari": {{
      "dis_cap_olcumleri": [
        {{
          "referans_deger_mm": 0.00,
          "olculen_deger": {{"ic_mm": null, "orta_mm": 0.00, "dis_mm": null}},
          "sapma": {{"ic_mm": null, "orta_mm": 0.00, "dis_mm": null}},
          "olcum_belirsizligi_mm": 0.030
        }},
        {{
          "referans_deger_mm": 50.00,
          "olculen_deger": {{"ic_mm": 50.00, "orta_mm": null, "dis_mm": 50.00}},
          "sapma": {{"ic_mm": 0.00, "orta_mm": null, "dis_mm": 0.00}},
          "olcum_belirsizligi_mm": 0.030
        }}
      ],
      "ic_cap_olcumleri": [
        {{
          "referans_deger_mm": 20.00,
          "olculen_deger_mm": 20.02,
          "sapma_mm": 0.02,
          "olcum_belirsizligi_mm": 0.030
        }}
      ],
      "derinlik_olcumleri": [],
      "kademe_olcumleri": []
    }},
    "uygunluk_degerlendirmesi": {{
      "karar_kurali": "VDI/VDE/DGQ 2618 bölüm 9.1 de verilen tolerans değerlerine göre uygundur",
      "aciklamalar": [
        "Kalibrasyon sonuçları sadece test edilen cihaza ait olup kalibrasyon tarihinden itibaren belirtilmiş şartlarda geçerlidir.",
        "Bu sertifikada verilen sonuçlar cihazın kalibrasyon tarihindeki durumuna ait olup cihazın uzun dönem kararlılığını içermez.",
        "Cihazın performansı için gerekli çevre şartlarında kullanımından ve gelecek kalibrasyon tarihinden kullanıcı sorumludur."
      ],
      "olcum_belirsizligi_aciklama": "Beyan edilen genişletilmiş ölçüm belirsizliği standart belirsizliğin k=2 olarak alınan genişletme katsayısı ile çarpımı sonucunda bulunan değerdir ve %95 oranında güvenilirlik sağlamaktadır."
    }},
    "onay_bilgileri": {{
      "yayim_tarihi": "{datetime.now().strftime('%d.%m.%Y')}",
      "kalibrasyonu_yapan": {{
        "isim": "Mutlu YAVUZ",
        "unvan": "Kalibrasyon Personeli"
      }},
      "onaylayan": {{
        "isim": "Abdullah ÖZTÜRK",
        "unvan": "Teknik Müdür",
        "tarih": "{datetime.now().strftime('%d.%m.%Y')}"
      }}
    }},
    "standartlar": {{
      "akreditasyon_standardi": "TS EN ISO/IEC 17025:2017",
      "uluslararasi_anlasma": [
        "Avrupa Akreditasyon Birliği (EA) - Çok Taraflı Anlaşma (MLA)",
        "Uluslararası Laboratuvar Akreditasyon Birliği (ILAC) - Karşılıklı Tanıma Anlaşması (MRA)"
      ]
    }}
  }}
}}

ÖNEMLI: Ses kaydından çıkarabileceğin bilgileri kullan, yoksa yukarıdaki varsayılan değerleri kullan.
Sadece geçerli JSON döndür, başka açıklama ekleme.
"""
        
        # OpenAI API çağrısını thread pool'da çalıştır
        def generate_with_gpt():
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Sen bir muayene raporu analisti asistanısın. Verilen metinden yapılandırılmış JSON verisi çıkarırsın. Sadece geçerli JSON döndür."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(executor, generate_with_gpt)
        
        report_json = json.loads(response.choices[0].message.content)
        
        return report_json
    
    except Exception as e:
        # Hata durumunda fallback olarak kalibrasyon sertifikası formatında demo data döndür
        print(f"GPT HATA: {str(e)}")
        return {
            "kalibrasyon_sertifikasi": {
                "sertifika_bilgileri": {
                    "firma": "AS KALİBRASYON İÇ VE DIŞ TİCARET SAN. PAZ. LTD.ŞTİ.",
                    "adres": "Meriç Mahallesi 5747/10 Sokak No:12/2 Bornova / İZMİR",
                    "telefon": "232 247 07 44",
                    "faks": "232 431 07 44",
                    "email": "satis@askalibrasyon.com",
                    "website": "www.askalibrasyon.com",
                    "akreditasyon_no": "AB-0068-K",
                    "sertifika_no": f"KAL-DEMO-{datetime.now().strftime('%Y%m%d-%H%M')}",
                    "tarih": datetime.now().strftime('%d.%m.%Y')
                },
                "musteri_bilgileri": {
                    "sahibi": "TEST MÜŞTERİSİ",
                    "adres": "Demo adres - GPT hatası",
                    "istek_numarasi": f"İ-DEMO-{datetime.now().strftime('%y-%m%d')} / 1"
                },
                "cihaz_bilgileri": {
                    "makine_cihaz": "KUMPAS (Demo)",
                    "imalatci": "-",
                    "tip": "VERNİYERLİ",
                    "seri_numarasi": "DEMO-001",
                    "kalibrasyon_tarihi": datetime.now().strftime('%d.%m.%Y'),
                    "sayfa_sayisi": 2,
                    "olcme_araligi": "0-150 mm",
                    "cozunurluk": "0.01 mm"
                },
                "kalibrasyon_detaylari": {
                    "laboratuvara_kabul_tarihi": datetime.now().strftime('%d.%m.%Y'),
                    "yontem_prosedur": "DEMO - GPT hatası nedeniyle varsayılan veri",
                    "cevre_sartlari": {
                        "sicaklik": "20 ± 1°C",
                        "bagil_nem": "%45 ± 25 %rh",
                        "aciklama": f"Orijinal ses kaydı: {request.text[:100]}..."
                    }
                },
                "referans_cihazlar": [],
                "fonksiyonellik_kontrolu": {
                    "olcme_ceneleri": "Demo",
                    "tespitleme_vidasi": "Demo",
                    "gosterge": "Demo",
                    "tambur_yatak_boslugu": "-",
                    "ic_cap_olcme_ceneleri": "-",
                    "derinlik_olcme_ceneleri": "-"
                },
                "olcum_sonuclari": {
                    "dis_cap_olcumleri": [],
                    "ic_cap_olcumleri": [],
                    "derinlik_olcumleri": [],
                    "kademe_olcumleri": []
                },
                "uygunluk_degerlendirmesi": {
                    "karar_kurali": "DEMO VERİ - GPT hatası",
                    "aciklamalar": [f"GPT Hatası: {str(e)}"],
                    "olcum_belirsizligi_aciklama": "Demo veri"
                },
                "onay_bilgileri": {
                    "yayim_tarihi": datetime.now().strftime('%d.%m.%Y'),
                    "kalibrasyonu_yapan": {
                        "isim": "Demo Personel",
                        "unvan": "Kalibrasyon Personeli"
                    },
                    "onaylayan": {
                        "isim": "Demo Müdür",
                        "unvan": "Teknik Müdür",
                        "tarih": datetime.now().strftime('%d.%m.%Y')
                    }
                }
            }
        }


@app.post("/api/create-pdf")
async def create_pdf(report: ReportData):
    """
    Rapor verisinden profesyonel PDF oluşturur (fpdf2 ile - Türkçe tam destek)
    """
    try:
        # Rapor numarası oluştur
        rapor_no = f"RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # PDF dosya adı
        filename = f"rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = UPLOAD_DIR / filename
        
        # PDF oluştur
        pdf = FPDF()
        pdf.add_page()
        
        # Türkçe font ekle (DejaVu Sans yoksa atlayacak)
        try:
            pdf.add_font('DejaVu', '', 'C:/Windows/Fonts/DejaVuSans.ttf')
            pdf.add_font('DejaVu', 'B', 'C:/Windows/Fonts/DejaVuSans-Bold.ttf')
            pdf.set_font('DejaVu', '', 10)
            print("DejaVu Sans fontu yüklendi")
        except:
            # DejaVu yoksa Arial kullan
            pdf.add_font('Arial', '', 'C:/Windows/Fonts/arial.ttf')
            pdf.add_font('Arial', 'B', 'C:/Windows/Fonts/arialbd.ttf')
            pdf.set_font('Arial', '', 10)
            print("Arial fontu kullanılıyor")
        
        # Başlık
        pdf.set_font('DejaVu', 'B', 18) if 'DejaVu' in pdf.fonts else pdf.set_font('Arial', 'B', 18)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 10, 'MUAYENE RAPORU', ln=True, align='C')
        pdf.set_font('DejaVu', '', 11) if 'DejaVu' in pdf.fonts else pdf.set_font('Arial', '', 11)
        pdf.set_text_color(127, 140, 141)
        pdf.cell(0, 8, 'ISO/IEC 17020 Uyumlu Kalibrasyon Raporu', ln=True, align='C')
        pdf.ln(2)
        
        font_name = 'DejaVu' if 'DejaVu' in pdf.fonts else 'Arial'
        
        # GENEL BİLGİLER
        pdf.set_font(font_name, 'B', 12)
        pdf.set_text_color(44, 62, 80)
        pdf.set_fill_color(248, 249, 250)
        pdf.cell(0, 10, 'GENEL BİLGİLER', ln=True, fill=True, border=1)
        pdf.set_font(font_name, '', 10)
        pdf.set_text_color(0, 0, 0)
        
        genel_data = [
            ['Rapor No:', rapor_no],
            ['Muayene Türü:', report.muayene_turu],
            ['Tarih:', report.tarih],
            ['Teknisyen:', report.teknisyen],
        ]
        
        for label, value in genel_data:
            pdf.set_fill_color(232, 244, 248)
            pdf.set_font(font_name, 'B', 10)
            pdf.cell(50, 8, label, border=1, fill=True)
            pdf.set_font(font_name, '', 10)
            pdf.cell(0, 8, value, border=1, ln=True)
        
        pdf.ln(2)
        
        # CİHAZ BİLGİLERİ
        pdf.set_font(font_name, 'B', 12)
        pdf.set_text_color(44, 62, 80)
        pdf.set_fill_color(248, 249, 250)
        pdf.cell(0, 10, 'CİHAZ BİLGİLERİ', ln=True, fill=True, border=1)
        pdf.set_font(font_name, '', 10)
        pdf.set_text_color(0, 0, 0)
        
        cihaz_data = [
            ['Marka:', report.cihaz_bilgileri.get('marka', '-')],
            ['Model:', report.cihaz_bilgileri.get('model', '-')],
            ['Seri No:', report.cihaz_bilgileri.get('seri_no', '-')],
        ]
        
        for label, value in cihaz_data:
            pdf.set_fill_color(232, 244, 248)
            pdf.set_font(font_name, 'B', 10)
            pdf.cell(50, 8, label, border=1, fill=True)
            pdf.set_font(font_name, '', 10)
            pdf.cell(0, 8, value, border=1, ln=True)
        
        pdf.ln(2)
        
        # GÖRSEL ANALİZ
        if report.gorsel_analiz:
            pdf.set_font(font_name, 'B', 12)
            pdf.set_text_color(44, 62, 80)
            pdf.set_fill_color(255, 249, 230)
            pdf.cell(0, 10, 'GÖRSEL ANALİZ SONUÇLARI', ln=True, fill=True, border=1)
            pdf.set_font(font_name, '', 10)
            pdf.set_text_color(0, 0, 0)
            
            gorsel_data = [
                ['Cihaz Türü:', report.gorsel_analiz.get('cihaz_turu', '-')],
                ['Görsel Durum:', report.gorsel_analiz.get('gorsel_durum', '-')],
            ]
            
            if report.gorsel_analiz.get('gosterge_deger'):
                gorsel_data.append(['Gösterge Değeri:', str(report.gorsel_analiz.get('gosterge_deger'))])
            
            if report.gorsel_analiz.get('anomaliler'):
                anomaliler_str = ', '.join(report.gorsel_analiz.get('anomaliler', []))
                gorsel_data.append(['Anomaliler:', anomaliler_str])
            
            if report.gorsel_analiz.get('oneriler'):
                oneriler_str = ', '.join(report.gorsel_analiz.get('oneriler', []))
                gorsel_data.append(['Öneriler:', oneriler_str])
            
            for label, value in gorsel_data:
                pdf.set_fill_color(255, 249, 230)
                pdf.set_font(font_name, 'B', 10)
                pdf.cell(50, 8, label, border=1, fill=True)
                pdf.set_font(font_name, '', 10)
                pdf.multi_cell(0, 8, value, border=1)
            
            pdf.ln(2)
        
        # ÖLÇÜM SONUÇLARI
        pdf.set_font(font_name, 'B', 12)
        pdf.set_text_color(44, 62, 80)
        pdf.set_fill_color(248, 249, 250)
        pdf.cell(0, 10, 'ÖLÇÜM SONUÇLARI', ln=True, fill=True, border=1)
        
        # Tablo başlığı
        pdf.set_fill_color(44, 62, 80)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(font_name, 'B', 10)
        pdf.cell(60, 10, 'Parametre', border=1, fill=True)
        pdf.cell(70, 10, 'Ölçülen Değer', border=1, fill=True)
        pdf.cell(60, 10, 'Durum', border=1, fill=True, ln=True)
        
        # Tablo içeriği
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_name, '', 10)
        for parametre, deger in report.olcum_sonuclari.items():
            pdf.cell(60, 8, parametre, border=1)
            pdf.cell(70, 8, str(deger), border=1)
            pdf.cell(60, 8, 'Normal', border=1, ln=True)
        
        pdf.ln(2)
        
        # NOTLAR
        pdf.set_font(font_name, 'B', 12)
        pdf.set_text_color(44, 62, 80)
        pdf.set_fill_color(255, 249, 230)
        pdf.cell(0, 10, 'NOTLAR VE GÖZLEMLER', ln=True, fill=True, border=1)
        pdf.set_font(font_name, '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 6, report.notlar, border=1)
        
        pdf.ln(1)
        
        # İMZA ALANI
        pdf.set_font(font_name, 'B', 10)
        pdf.cell(95, 8, 'Muayene Yapan', border=0, align='C')
        pdf.cell(95, 8, 'Onaylayan', border=0, align='C', ln=True)
        pdf.ln(1)
        pdf.set_font(font_name, '', 10)
        pdf.cell(95, 8, report.teknisyen, border='T', align='C')
        pdf.cell(95, 8, '_____________________', border='T', align='C', ln=True)
        pdf.cell(95, 6, f'Tarih: {report.tarih}', border=0, align='C')
        pdf.cell(95, 6, 'İmza ve Tarih', border=0, align='C', ln=True)
        
        pdf.ln(1)
        
        # Footer
        pdf.set_font(font_name, '', 9)
        pdf.set_text_color(127, 140, 141)
        pdf.cell(0, 5, 'DIKKAT: Bu rapor izinsiz çoğaltılamaz ve değiştirilemez.', ln=True, align='C')
        pdf.cell(0, 5, 'Bu belge elektronik olarak oluşturulmuştur.', ln=True, align='C')
        pdf.cell(0, 5, f'Rapor No: {rapor_no} | Oluşturulma Tarihi: {report.tarih}', ln=True, align='C')
        
        # PDF'i kaydet
        pdf.output(str(pdf_path))
        
        return FileResponse(
            path=str(pdf_path),
            media_type='application/pdf',
            filename=filename
        )
    
    except Exception as e:
        import traceback
        print(f"PDF HATA: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PDF oluşturma hatası: {str(e)}")


@app.post("/api/create-kalibrasyon-pdf")
async def create_kalibrasyon_pdf(data: KalibrasyonSertifikasiData):
    """
    Kalibrasyon sertifikası PDF'i oluşturur (ISO 17020 formatında)
    """
    try:
        cert = data.kalibrasyon_sertifikasi
        
        # PDF dosya adı
        filename = f"kalibrasyon_sertifikasi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = UPLOAD_DIR / filename
        
        # PDF oluştur - Yatay sayfa (landscape) kullan, marjinleri minimize et
        pdf = FPDF(orientation='L', unit='mm', format='A4')  # 'L' = Landscape
        pdf.set_auto_page_break(auto=True, margin=8)  # Daha az marjin
        pdf.set_left_margin(8)
        pdf.set_right_margin(8)
        pdf.set_top_margin(8)
        pdf.add_page()
        
        # Türkçe font ekle
        try:
            pdf.add_font('DejaVu', '', 'C:/Windows/Fonts/DejaVuSans.ttf')
            pdf.add_font('DejaVu', 'B', 'C:/Windows/Fonts/DejaVuSans-Bold.ttf')
            font_name = 'DejaVu'
        except:
            pdf.add_font('Arial', '', 'C:/Windows/Fonts/arial.ttf')
            pdf.add_font('Arial', 'B', 'C:/Windows/Fonts/arialbd.ttf')
            font_name = 'Arial'
        
        # BAŞLIK - ŞİRKET BİLGİLERİ
        sert_bilgi = cert.get('sertifika_bilgileri', {})
        
        pdf.set_font(font_name, 'B', 14)
        pdf.set_text_color(30, 58, 138)
        pdf.multi_cell(0, 5, sert_bilgi.get('firma', ''), align='C')
        
        pdf.set_font(font_name, '', 8)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 4, sert_bilgi.get('adres', ''), ln=True, align='C')
        pdf.cell(0, 4, f"Tel: {sert_bilgi.get('telefon', '')} Faks: {sert_bilgi.get('faks', '')}", ln=True, align='C')
        pdf.cell(0, 4, f"E-posta: {sert_bilgi.get('email', '')} Web: {sert_bilgi.get('website', '')}", ln=True, align='C')
        pdf.ln(2)
        
        # Akreditasyon bilgisi
        pdf.set_font(font_name, 'B', 9)
        pdf.cell(0, 5, f"Akreditasyon No: {sert_bilgi.get('akreditasyon_no', '')}", ln=True, align='C')
        pdf.ln(2)
        
        # KALİBRASYON SERTİFİKASI başlığı
        pdf.set_font(font_name, 'B', 16)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 10, 'KALİBRASYON SERTİFİKASI', ln=True, align='C')
        pdf.ln(2)
        
        # Sertifika No ve Tarih
        pdf.set_font(font_name, 'B', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, f"Sertifika No: {sert_bilgi.get('sertifika_no', '')}       Tarih: {sert_bilgi.get('tarih', '')}", ln=True, align='C')
        pdf.ln(2)
        
        # MÜŞTERİ BİLGİLERİ
        musteri = cert.get('musteri_bilgileri', {})
        
        # Yeterli yer var mı kontrol et
        if pdf.get_y() > 170:
            pdf.add_page()
        
        pdf.set_font(font_name, 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 7, 'MÜŞTERİ BİLGİLERİ', ln=True, fill=True, border=1)
        pdf.set_font(font_name, '', 9)
        
        pdf.cell(45, 6, 'Sahibi:', border=1)
        pdf.cell(0, 6, musteri.get('sahibi', ''), border=1, ln=True)
        pdf.cell(45, 6, 'Adres:', border=1)
        pdf.cell(0, 6, musteri.get('adres', ''), border=1, ln=True)
        pdf.cell(45, 6, 'İstek Numarası:', border=1)
        pdf.cell(0, 6, musteri.get('istek_numarasi', ''), border=1, ln=True)
        pdf.ln(1)
        
        # CİHAZ BİLGİLERİ
        cihaz = cert.get('cihaz_bilgileri', {})
        pdf.set_font(font_name, 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 7, 'CİHAZ BİLGİLERİ', ln=True, fill=True, border=1)
        pdf.set_font(font_name, '', 9)
        
        cihaz_fields = [
            ('Makine/Cihaz:', cihaz.get('makine_cihaz', '')),
            ('İmalatçı:', cihaz.get('imalatci', '')),
            ('Tip:', cihaz.get('tip', '')),
            ('Seri Numarası:', cihaz.get('seri_numarasi', '')),
            ('Kalibrasyon Tarihi:', cihaz.get('kalibrasyon_tarihi', '')),
            ('Ölçme Aralığı:', cihaz.get('olcme_araligi', '')),
            ('Çözünürlük:', cihaz.get('cozunurluk', '')),
        ]
        
        for label, value in cihaz_fields:
            pdf.cell(50, 6, label, border=1)
            pdf.cell(0, 6, str(value), border=1, ln=True)
        pdf.ln(1)
        
        # ÇEVRE ŞARTLARI
        kal_detay = cert.get('kalibrasyon_detaylari', {})
        cevre = kal_detay.get('cevre_sartlari', {})
        
        pdf.set_font(font_name, 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 7, 'ÇEVRE ŞARTLARI', ln=True, fill=True, border=1)
        pdf.set_font(font_name, '', 9)
        
        pdf.cell(50, 6, 'Sıcaklık:', border=1)
        pdf.cell(0, 6, cevre.get('sicaklik', ''), border=1, ln=True)
        pdf.cell(50, 6, 'Bağıl Nem:', border=1)
        pdf.cell(0, 6, cevre.get('bagil_nem', ''), border=1, ln=True)
        pdf.ln(1)
        
        # FONKSİYONELLİK KONTROLÜ
        fonk = cert.get('fonksiyonellik_kontrolu', {})
        if fonk:
            pdf.set_font(font_name, 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 7, 'FONKSİYONELLİK KONTROLÜ', ln=True, fill=True, border=1)
            pdf.set_font(font_name, '', 9)
            
            for kontrol, durum in fonk.items():
                pdf.cell(95, 6, kontrol.replace('_', ' ').title() + ':', border=1)
                pdf.cell(0, 6, str(durum), border=1, ln=True)
            pdf.ln(1)
        
        # ÖLÇÜM SONUÇLARI - Yeterli yer varsa aynı sayfada devam et
        if pdf.get_y() > 160:  # Sayfa sonuna yaklaşıldıysa
            pdf.add_page()
        else:
            pdf.ln(3)  # Biraz boşluk
        
        pdf.set_font(font_name, 'B', 12)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 8, 'ÖLÇÜM SONUÇLARI', ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)
        
        olcum = cert.get('olcum_sonuclari', {})
        
        # DIŞ ÇAP ÖLÇÜMLERİ
        if 'dis_cap_olcumleri' in olcum:
            pdf.set_font(font_name, 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 7, 'DIŞ ÇAP ÖLÇÜMLERİ', ln=True, fill=True, border=1)
            
            # Tablo başlıkları - sütun genişliklerini küçülttük
            pdf.set_font(font_name, 'B', 7)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(24, 8, 'Referans', border=1, fill=True, align='C')
            pdf.cell(24, 8, 'İç', border=1, fill=True, align='C')
            pdf.cell(24, 8, 'Orta', border=1, fill=True, align='C')
            pdf.cell(24, 8, 'Dış', border=1, fill=True, align='C')
            pdf.cell(26, 8, 'Sapma İç', border=1, fill=True, align='C')
            pdf.cell(26, 8, 'Sapma Orta', border=1, fill=True, align='C')
            pdf.cell(22, 8, 'Belirsizlik', border=1, fill=True, align='C', ln=True)
            
            # Veriler
            pdf.set_font(font_name, '', 7)
            for olc in olcum['dis_cap_olcumleri']:
                ref = olc.get('referans_deger_mm', '')
                oc = olc.get('olculen_deger', {})
                sap = olc.get('sapma', {})
                bel = olc.get('olcum_belirsizligi_mm', '')
                
                pdf.cell(24, 7, str(ref) if ref else '-', border=1, align='C')
                pdf.cell(24, 7, str(oc.get('ic_mm')) if oc.get('ic_mm') is not None else '-', border=1, align='C')
                pdf.cell(24, 7, str(oc.get('orta_mm')) if oc.get('orta_mm') is not None else '-', border=1, align='C')
                pdf.cell(24, 7, str(oc.get('dis_mm')) if oc.get('dis_mm') is not None else '-', border=1, align='C')
                pdf.cell(26, 7, str(sap.get('ic_mm')) if sap.get('ic_mm') is not None else '-', border=1, align='C')
                pdf.cell(26, 7, str(sap.get('orta_mm')) if sap.get('orta_mm') is not None else '-', border=1, align='C')
                pdf.cell(22, 7, str(bel) if bel else '-', border=1, align='C', ln=True)
            pdf.ln(1)
        
        # İÇ ÇAP ÖLÇÜMLERİ
        if 'ic_cap_olcumleri' in olcum:
            pdf.set_font(font_name, 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 7, 'İÇ ÇAP ÖLÇÜMLERİ', ln=True, fill=True, border=1)
            
            pdf.set_font(font_name, 'B', 8)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(47, 8, 'Referans Değer (mm)', border=1, fill=True, align='C')
            pdf.cell(47, 8, 'Ölçülen Değer (mm)', border=1, fill=True, align='C')
            pdf.cell(47, 8, 'Sapma (mm)', border=1, fill=True, align='C')
            pdf.cell(47, 8, 'Belirsizlik (mm)', border=1, fill=True, align='C', ln=True)
            
            pdf.set_font(font_name, '', 8)
            for olc in olcum['ic_cap_olcumleri']:
                pdf.cell(47, 7, str(olc.get('referans_deger_mm', '')), border=1, align='C')
                pdf.cell(47, 7, str(olc.get('olculen_deger_mm', '')), border=1, align='C')
                pdf.cell(47, 7, str(olc.get('sapma_mm', '')), border=1, align='C')
                pdf.cell(47, 7, str(olc.get('olcum_belirsizligi_mm', '')), border=1, align='C', ln=True)
            pdf.ln(1)
        
        # DERİNLİK ÖLÇÜMLERİ
        if 'derinlik_olcumleri' in olcum:
            pdf.set_font(font_name, 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 7, 'DERİNLİK ÖLÇÜMLERİ', ln=True, fill=True, border=1)
            
            pdf.set_font(font_name, 'B', 8)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(47, 8, 'Referans Değer (mm)', border=1, fill=True, align='C')
            pdf.cell(47, 8, 'Ölçülen Değer (mm)', border=1, fill=True, align='C')
            pdf.cell(47, 8, 'Sapma (mm)', border=1, fill=True, align='C')
            pdf.cell(47, 8, 'Belirsizlik (mm)', border=1, fill=True, align='C', ln=True)
            
            pdf.set_font(font_name, '', 8)
            for olc in olcum['derinlik_olcumleri']:
                pdf.cell(47, 7, str(olc.get('referans_deger_mm', '')), border=1, align='C')
                pdf.cell(47, 7, str(olc.get('olculen_deger_mm', '')), border=1, align='C')
                pdf.cell(47, 7, str(olc.get('sapma_mm', '')), border=1, align='C')
                pdf.cell(47, 7, str(olc.get('olcum_belirsizligi_mm', '')), border=1, align='C', ln=True)
            pdf.ln(1)
        
        # KADEME ÖLÇÜMLERİ
        if 'kademe_olcumleri' in olcum:
            pdf.set_font(font_name, 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 7, 'KADEME ÖLÇÜMLERİ', ln=True, fill=True, border=1)
            
            pdf.set_font(font_name, 'B', 8)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(47, 8, 'Referans Değer (mm)', border=1, fill=True, align='C')
            pdf.cell(47, 8, 'Ölçülen Değer (mm)', border=1, fill=True, align='C')
            pdf.cell(47, 8, 'Sapma (mm)', border=1, fill=True, align='C')
            pdf.cell(47, 8, 'Belirsizlik (mm)', border=1, fill=True, align='C', ln=True)
            
            pdf.set_font(font_name, '', 8)
            for olc in olcum['kademe_olcumleri']:
                pdf.cell(47, 7, str(olc.get('referans_deger_mm', '')), border=1, align='C')
                pdf.cell(47, 7, str(olc.get('olculen_deger_mm', '')), border=1, align='C')
                pdf.cell(47, 7, str(olc.get('sapma_mm', '')), border=1, align='C')
                pdf.cell(47, 7, str(olc.get('olcum_belirsizligi_mm', '')), border=1, align='C', ln=True)
            pdf.ln(2)
        
        # UYGUNLUK DEĞERLENDİRMESİ
        uygunluk = cert.get('uygunluk_degerlendirmesi', {})
        if uygunluk:
            # Landscape A4: height=210mm, margin=10mm, usable=190mm
            # 175mm'den sonra yer kalmıyor, yeni sayfa aç
            if pdf.get_y() > 175:
                pdf.add_page()
            
            pdf.set_font(font_name, 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 7, 'UYGUNLUK DEĞERLENDİRMESİ', ln=True, fill=True, border=1)
            pdf.set_font(font_name, '', 7)
            
            try:
                pdf.multi_cell(0, 5, uygunluk.get('karar_kurali', ''), border=1)
            except:
                pdf.add_page()
                pdf.multi_cell(0, 5, uygunluk.get('karar_kurali', ''), border=1)
            pdf.ln(2)
            
            if 'aciklamalar' in uygunluk:
                for aciklama in uygunluk['aciklamalar']:
                    if pdf.get_y() > 175:
                        pdf.add_page()
                    try:
                        pdf.multi_cell(0, 4, '- ' + aciklama, border=0)
                    except:
                        pdf.add_page()
                        pdf.multi_cell(0, 4, '- ' + aciklama, border=0)
            pdf.ln(2)
            
            if 'olcum_belirsizligi_aciklama' in uygunluk:
                if pdf.get_y() > 175:
                    pdf.add_page()
                try:
                    pdf.multi_cell(0, 4, uygunluk['olcum_belirsizligi_aciklama'], border=0)
                except:
                    pdf.add_page()
                    pdf.multi_cell(0, 4, uygunluk['olcum_belirsizligi_aciklama'], border=0)
            pdf.ln(1)
        
        # ONAY BİLGİLERİ
        onay = cert.get('onay_bilgileri', {})
        if onay:
            pdf.ln(1)
            pdf.set_font(font_name, 'B', 9)
            
            # İki sütun için
            col_width = pdf.w / 2 - 20
            
            pdf.cell(col_width, 6, 'Kalibrasyonu Yapan:', border=0)
            pdf.cell(col_width, 6, 'Onaylayan:', border=0, ln=True)
            pdf.ln(1)
            
            pdf.set_font(font_name, '', 9)
            yapan = onay.get('kalibrasyonu_yapan', {})
            onaylayan = onay.get('onaylayan', {})
            
            pdf.cell(col_width, 6, yapan.get('isim', ''), border='T', align='C')
            pdf.cell(col_width, 6, onaylayan.get('isim', ''), border='T', align='C', ln=True)
            
            pdf.cell(col_width, 5, yapan.get('unvan', ''), border=0, align='C')
            pdf.cell(col_width, 5, onaylayan.get('unvan', ''), border=0, align='C', ln=True)
            
            if 'tarih' in onaylayan:
                pdf.cell(col_width, 5, '', border=0)
                pdf.cell(col_width, 5, f"Tarih: {onaylayan.get('tarih', '')}", border=0, align='C', ln=True)
        
        # Footer
        pdf.ln(2)
        pdf.set_font(font_name, '', 7)
        pdf.set_text_color(100, 100, 100)
        standartlar = cert.get('standartlar', {})
        if standartlar:
            pdf.multi_cell(0, 3, f"Bu sertifika {standartlar.get('akreditasyon_standardi', '')} standardına göre düzenlenmiştir.", align='C')
        
        # PDF'i kaydet
        pdf.output(str(pdf_path))
        
        return FileResponse(
            path=str(pdf_path),
            media_type='application/pdf',
            filename=filename
        )
    
    except Exception as e:
        import traceback
        print(f"KALİBRASYON PDF HATA: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Kalibrasyon PDF oluşturma hatası: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

