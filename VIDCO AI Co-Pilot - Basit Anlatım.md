# VIDCO AI Co‑Pilot — Uzun Rapor Yazarı (Spec + Yol Haritası)

Aşağıdaki doküman, **uzun ve profesyonel raporları** (10–30+ sayfa) rahatça üreten, hataya dayanıklı, kullanıcı dostu bir **Flutter Web + FastAPI** uygulaması için kapsamlı tasarım ve uygulama planıdır. Mevcut mimarinize (Whisper, GPT‑4o‑mini, Vision, xhtml2pdf/Jinja2) tam uyumludur.

---

## 0) Ürün Hedefi

* **Hızlı taslak**: Ses → Transkript → Bölümlenmiş yapılandırılmış taslak
* **Derinleştirme**: Bölüm bazlı genişletme, referans/ek veri ekleme
* **Görsel entegrasyon**: Cihaz fotoğrafları, ölçüm ekran görüntüleri, tablo/grafik
* **Kurumsal format**: ISO/IEC 17020 uyumlu ve kurum şablonlarına göre varyant
* **Uzun rapor ergonomisi**: Bölüm katmanları, outline, sürümler, autosave, geri al/ilerle

---

## 1) UX / Editör Tasarımı

**Amaç: Kullanıcıyı metinle boğmadan, “bölüm-bölüm” akış sağlamak.**

### 1.1 Bölümlü Rapor Editörü

* Sol panel: **Outline (İçindekiler)** – başlıklar, alt başlıklar, check‑status (✓/in-progress)
* Orta panel: **Zengin editör** – Markdown + toolbar (başlık, bold, tablo, liste)
* Sağ panel: **Yardımcı asistan** – bölüm için prompt alanı + “Genişlet / Özetle / Netleştir / Dil düzelt” butonları
* Üst bar: **Kaydet durumu**, versiyon adı (örn. v1.2), **PDF Önizleme** butonu, **Rapor Ayarları**

### 1.2 Uzun Metin Rahatlığı

* **Otomatik başlık/satır numarası** (opsiyonel)
* **300–500 sözcükte bir autosave** (debounce ile)
* **Kayan outline**: Seçili bölüm highlight
* **Çakışma koruması**: Başka cihazda açıkken uyarı + “kopyasını oluştur”
* **Sürümleme**: Commit mesajı ile anlık “snapshot” (v1.3 – “Ölçüm sonuçları eklendi”)

### 1.3 Hızlı Eylemler (AI)

* Bölüm menüsü: **Genişlet (x kelime)**, **Tablo Oluştur**, **Ölçümleri maddele**, **Kaynakça öner**, **Dil denetimi (TR/EN)**
* Global menü: **Tam raporu tutarlılaştır** (terminoloji, birim, yazım)

---

## 2) Veri Modeli (DB + API Sözleşmesi)

### 2.1 Pydantic Şemaları

```python
# backend/models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Measurement(BaseModel):
    name: str
    value: str
    unit: Optional[str] = None
    reference: Optional[str] = None

class DeviceInfo(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_no: Optional[str] = None
    type: Optional[str] = None

class Section(BaseModel):
    id: str
    title: str
    content_md: str = ""
    status: str = Field(default="in_progress", description="in_progress|done")

class VisionFinding(BaseModel):
    image_path: str
    findings: List[str] = []
    anomalies: List[str] = []
    gauge_readings: List[str] = []

class Report(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    report_no: str
    case_type: Optional[str] = None  # Muayene türü
    technician: Optional[str] = None
    device: DeviceInfo = DeviceInfo()
    measurements: List[Measurement] = []
    notes: List[str] = []
    sections: List[Section] = []
    vision: List[VisionFinding] = []
    version: str = "v1.0"
```

> Not: DB olarak **MongoDB** veya **PostgreSQL (JSONB)** önerilir. `reports`, `report_versions`, `uploads` koleksiyon/tabloları.

### 2.2 API Uçları (FastAPI)

* `POST /api/reports` → yeni rapor (boş şablon/varsayılan bölümlerle)
* `GET /api/reports/{id}` → rapor verisi
* `PATCH /api/reports/{id}` → meta güncelle (teknisyen, cihaz, ölçümler…)
* `PATCH /api/reports/{id}/section/{sid}` → **bölüm içeriği** (autosave endpoint)
* `POST /api/reports/{id}/ai/expand` → seçili bölüm prompt’u ile genişlet
* `POST /api/reports/{id}/ai/refine` → dil denetimi / tutarlılık
* `POST /api/reports/{id}/vision` → görsel analizi çalıştır (dosya referansı ile)
* `POST /api/reports/{id}/pdf` → PDF üret (senkron) veya `POST /jobs/pdf` (asenkron job)
* `GET /api/reports/{id}/pdf` → son PDF indir
* `POST /uploads` → pre‑signed URL/stream upload (foto, ek, csv)
* `GET /reports?query=…&page=…` → geçmiş raporlar listesi

---

## 3) PDF Şablon Stratejisi (Jinja2 + xhtml2pdf)

### 3.1 Şablon Parçaları

* `base.html` – kurumsal header/footer, sayfa numarası, logo, ISO/IEC 17020 bloğu
* `cover.html` – kapak (rapor no, tarih, firma, teknisyen)
* `toc.html` – otomatik içindekiler (başlık seviyelerine göre)
* `section.html` – **her bölüm için** tekrarlanan parça
* `vision.html` – foto + alt yazılar + tespit listeleri
* `appendix.html` – tablolar/grafikler/ham loglar

### 3.2 Uzun Rapor Optimizasyonu

* **Sayfa sonu kontrolü**: Başlık + ilk paragraf ayrılmasın (page-break-inside)
* **Yüksek DPI** resimler için max‑width ve kalite düşürme opsiyonu
* **Tablo stilleri**: zebra, otomatik kırılma, daraltma (word-wrap)

---

## 4) Görsel Analiz Entegrasyonu

### 4.1 Akış

1. Frontend foto yükler (`/uploads`) → path döner
2. `POST /api/reports/{id}/vision` çağrısı (path + opsiyonlar)
3. Backend **OpenAI Vision** ile: cihaz türü, hasar, gösterge okuması, anomaliler
4. Sonuç `vision[]` alanına eklenir, **vision.html**’de PDF’e basılır

### 4.2 Örnek Prompt (backend)

```python
VISION_SYSTEM = (
    "You are an expert calibration inspector. Analyze the device photo and extract: "
    "1) device type and identifiers, 2) visible wear/damage, 3) gauge/display readings "
    "with units if possible, 4) any anomalies, 5) actionable recommendations."
)
```

---

## 5) Uzun Metin Üretimi: Bölüm Bazlı ve Akıllı

### 5.1 Bölüm Kütüphanesi

* **Minimal zorunlu bölümler**: Amaç ve Kapsam, Metodoloji, Cihaz Bilgileri, Ölçüm Sonuçları, Değerlendirme, Sonuç/Öneriler, Ekler
* **Opsiyonel modüller**: Risk Analizi, Bakım Geçmişi, Standart Referanslar, Kalibrasyon Sertifikaları özeti

### 5.2 Bölüm Genişletme API’si (stream)

* **Chunked** yanıt: UI’da yazarken görünür, kullanıcı isterse durdurabilir
* **Kelime/karakter hedefi**: `target_words=600` gibi parametre
* **Stil rehberi**: Kurumsal/teknik, pasif/aktif ses, **TR/EN** anahtarları

### 5.3 Terminoloji/Tutarlılık Denetimi

* **Sözlük**: Birim, kısaltma, cihaz adı sözlüğü (JSON)
* `POST /ai/refine` çağrısında bu sözlükler prompt’a eklenir → tutarlı çıktı

---

## 6) Performans & Dayanıklılık

* **Autosave**: 2 sn debounce, failure retry (3x, expo backoff)
* **Offline tolerance**: IndexedDB cache; bağlantı geri gelince sync
* **Büyük raporlar**: Bölüm lazy‑load, sadece aktif bölüm render
* **Medya optimizasyonu**: Upload’da görselleri 1920px’e düşürme (opsiyon)
* **Arka plan işler**: PDF üretimi ve büyük Vision işler için Celery/RQ (opsiyonel)

---

## 7) Güvenlik & Uyumluluk

* **JWT auth** (rol: teknisyen, kontrolör, admin)
* **İmzalar**: Yetkili kullanıcılar için **e‑imza/ıslak imza alanı**
* **Loglama**: Önemli aksiyonlar (pdf üretildi, versiyon alındı, dışa aktarıldı)
* **Sürüm izi**: Kim, ne zaman, hangi bölüm değişti (audit trail)

---

## 8) Flutter Web Uygulama Mimarisi

```
lib/
 ├─ main.dart
 ├─ core/ (theme, routes, di)
 ├─ data/ (models dto, api clients)
 ├─ state/ (providers/cubits)
 ├─ widgets/ (editor, outline, ai-panel, pdf-preview)
 └─ screens/
     ├─ report_editor_page.dart
     ├─ reports_list_page.dart
     └─ settings_page.dart
```

### 8.1 Önemli Bileşenler

* **`OutlinePanel`**: Bölümleri listeler, drag‑drop ile sıralama
* **`MarkdownEditor`**: Ctrl+Kısayollar, tablo ekleyici, kelime sayacı
* **`AIAssistantPanel`**: prompt textarea + butonlar (Genişlet/Özetle/Refine)
* **`PdfPreviewPane`**: Son üretimi göster (Son PDF URL)
* **`AutosaveBanner`**: Kaydetme durumları

---

## 9) FastAPI — Örnek Uçlar (iskelet)

```python
# backend/main.py (özet)
from fastapi import FastAPI, UploadFile, Body
from models import Report, Section

app = FastAPI()

@app.post("/api/reports")
def create_report(meta: dict = Body(...)):
    # db insert, default sections
    return {"id": "...", "report_no": "VID-2025-0001"}

@app.get("/api/reports/{rid}")
def get_report(rid: str):
    # db fetch
    ...

@app.patch("/api/reports/{rid}/section/{sid}")
def update_section(rid: str, sid: str, payload: dict):
    # content_md update + updated_at
    ...

@app.post("/api/reports/{rid}/ai/expand")
def ai_expand(rid: str, sid: str, prompt: str, target_words: int = 400):
    # stream tokens → frontend
    ...

@app.post("/api/reports/{rid}/pdf")
def generate_pdf(rid: str):
    # render jinja → xhtml2pdf → save uploads/rapor.pdf
    return {"pdf_url": "/uploads/VID-2025-0001.pdf"}
```

---

## 10) Test Senaryoları (Kabul Kriterleri)

1. **30+ sayfa rapor**: Bölüm bölünmesi, içindekiler ve sayfa numaraları doğru
2. **Autosave**: İnternet kesilip gelince veri kaybı yok
3. **Vision**: En az 3 örnek foto için doğru tür, hasar ve gösterge okuması
4. **Tutarlılık**: Birimler (°C, mbar, V), tarih formatı (DD.MM.YYYY) tek tip
5. **PDF**: Kapak + imza alanları + ekler doğru hizalı ve taşmıyor

---

## 11) Yol Haritası (2+2 Hafta MVP++)

**Hafta 1–2 (MVP Uzun Rapor Yazarı)**

* Bölümlü editör + outline + autosave
* Bölüm bazlı AI genişletme/özetleme
* PDF şablonlarının parçalanması (base/section/toc)
* Vision endpoint iskeleti

**Hafta 3–4 (Pro)**

* Vision sonuçlarının PDF entegrasyonu
* Versiyonlama/snapshot + audit trail
* Büyük medya optimizasyonu + önizleme
* Rapor arama/filtre (teknisyen, tarih, cihaz)

---

## 12) Entegrasyonlar (Paylaşım)

* **E‑posta**: SMTP + imap‑send (raporu gönder, gönderim kaydı)
* **WhatsApp**: Link paylaşımı (rapor indir URL) + kısa özet
* **Kurumsal DMS**: S3/MinIO dizin yapısı: `/{yil}/{rapor_no}/` (pdf, imgs, json)

---

## 13) Hazır Prompt Paketleri (TR)

* **Bölüm Genişletme (Teknik/Resmi)**

```
Aşağıdaki bölüm taslağını, ISO/IEC 17020 üslubunda, teknik ve nesnel bir dil ile \n"
+ f"yaklaşık {{target_words}} kelime olacak şekilde genişlet. Terminoloji sözlüğüne uy: {TERMS}. \n"
+ "Rakamları birimlerle ver, gereksiz iddia kullanma, kaynağı belirsiz bilgiden kaçın.\n"
+ "Giriş cümlesi bağlam kurucu olsun, sonuç cümlesi kısa özet içersin."
```

* **Tutarlılık / Dil Denetimi**

```
Metni Türkçe teknik yazım kurallarına göre sadeleştir ve tutarlılaştır. \n"
+ "Kısaltmalar: {ABBREV}. Tarih: DD.MM.YYYY. Ondalık: virgül. \n"
+ "Birimler: SI. Marka/model/seri no biçimini koru."
```

---

## 14) Riskler ve Önlemler

* **xhtml2pdf limitleri** → tablo/görsel karmaşık ise wkhtmltopdf alternatifi hazırla
* **Uzun stream kesilmesi** → bölüm bazlı üretim + yerel cache + resume token
* **Görsel yorum hataları** → kullanıcıya manuel düzeltme alanı + “kanıt foto” referansı

---

## 15) Başarı Ölçütleri

* Rapor tamamlama süresi (dk)
* Geri dönüş/düzeltme sayısı
* PDF yeniden üretim hızı (sn)
* Kullanıcı memnuniyeti (NPS) ve hata oranı

---

**Sonuç:** Bu tasarım, uzun rapor üretimini bölüm bazlı, dayanıklı ve kurumsal uyumlu hale getirir. Mevcut stack’inizle minimum sürtünmeyle uygulanabilir; 2–4 haftada MVP++, 6–8 haftada enterprise seviyesine taşınabilir.
