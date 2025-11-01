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
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from io import BytesIO

# production.env dosyasını yükle
env_file = Path(__file__).parent / "production.env"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()  # .env dosyasını dene

app = FastAPI(title="VIDCO AI Co-Pilot Backend")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Dosya kaydetme dizini
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Template dizini
TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_DIR.mkdir(exist_ok=True)

# Jinja2 environment
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


class TranscriptionRequest(BaseModel):
    text: str


class ReportData(BaseModel):
    muayene_turu: str
    tarih: str
    teknisyen: str
    cihaz_bilgileri: dict
    olcum_sonuclari: dict
    notlar: str


@app.get("/")
async def root():
    return {"message": "VIDCO AI Co-Pilot Backend API", "status": "running"}


@app.post("/api/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    """
    Ses dosyasını metne çevirir (OpenAI Whisper kullanarak)
    """
    try:
        # Dosyayı kaydet
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # OpenAI Whisper ile transkripsiyon
        with open(file_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="tr"
            )
        
        # Dosyayı sil
        file_path.unlink()
        
        return {"text": transcript.text, "status": "success"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transkripsiyon hatası: {str(e)}")


@app.post("/api/generate-report")
async def generate_report(request: TranscriptionRequest):
    """
    Metinden rapor verisi oluşturur (GPT-4o kullanarak)
    """
    try:
        prompt = f"""
Aşağıdaki muayene ses kaydı metninden yapılandırılmış bir rapor oluştur.

Metin: {request.text}

JSON formatında şu bilgileri çıkar:
{{
    "muayene_turu": "Muayene türü (metinden çıkar, yoksa 'Kalibrasyon Muayenesi')",
    "tarih": "{datetime.now().strftime('%d.%m.%Y')}",
    "teknisyen": "Teknisyen adı (metinde varsa çıkar, yoksa 'Belirtilmemiş')",
    "cihaz_bilgileri": {{
        "marka": "Cihaz markası",
        "model": "Cihaz modeli",
        "seri_no": "Seri numarası"
    }},
    "olcum_sonuclari": {{
        "parametre1": "değer1",
        "parametre2": "değer2"
    }},
    "notlar": "Ek notlar ve gözlemler"
}}

Sadece geçerli JSON döndür, başka açıklama ekleme.
"""
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Daha hızlı ve ucuz model
            messages=[
                {"role": "system", "content": "Sen bir muayene raporu analisti asistanısın. Verilen metinden yapılandırılmış JSON verisi çıkarırsın. Sadece geçerli JSON döndür."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        report_json = json.loads(response.choices[0].message.content)
        
        return report_json
    
    except Exception as e:
        # Hata durumunda fallback olarak demo data döndür
        return {
            "muayene_turu": "Kalibrasyon Muayenesi",
            "tarih": datetime.now().strftime("%d.%m.%Y"),
            "teknisyen": "Belirtilmemiş",
            "cihaz_bilgileri": {
                "marka": "Test Cihazı",
                "model": "Demo",
                "seri_no": "DEMO-001"
            },
            "olcum_sonuclari": {
                "Durum": "GPT hatası - demo veri"
            },
            "notlar": f"Orijinal metin: {request.text}\n\nHata: {str(e)}"
        }


@app.post("/api/create-pdf")
async def create_pdf(report: ReportData):
    """
    Rapor verisinden profesyonel PDF oluşturur (xhtml2pdf + Jinja2)
    """
    try:
        # Rapor numarası oluştur
        rapor_no = f"RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Template'i yükle
        template = jinja_env.get_template('rapor_template.html')
        
        # HTML oluştur
        html_content = template.render(
            rapor_no=rapor_no,
            muayene_turu=report.muayene_turu,
            tarih=report.tarih,
            teknisyen=report.teknisyen,
            cihaz_bilgileri=report.cihaz_bilgileri,
            olcum_sonuclari=report.olcum_sonuclari,
            notlar=report.notlar
        )
        
        # PDF dosya adı
        filename = f"rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = UPLOAD_DIR / filename
        
        # HTML'den PDF oluştur
        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf_file,
                encoding='utf-8'
            )
        
        if pisa_status.err:
            raise Exception("PDF oluşturma hatası")
        
        return FileResponse(
            path=str(pdf_path),
            media_type='application/pdf',
            filename=filename
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF oluşturma hatası: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

