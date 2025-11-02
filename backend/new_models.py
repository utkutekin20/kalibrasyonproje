"""
Yeni sistem için veritabanı modelleri
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class DurumEnum(str, enum.Enum):
    DEVAM_EDIYOR = "devam_ediyor"
    TAMAMLANDI = "tamamlandi"
    IPTAL = "iptal"


class CihazTipiEnum(str, enum.Enum):
    KUMPAS = "kumpas"
    MIKROMETRE = "mikrometre"
    TERAZI = "terazi"
    BASINC_TRANSMITTERI = "basinc_transmitteri"
    SICAKLIK_OLCER = "sicaklik_olcer"
    MULTIMETRE = "multimetre"
    DIGER = "diger"


class Organizasyon(Base):
    """Kalibrasyon organizasyonu - birden fazla cihazı kapsayan iş paketi"""
    __tablename__ = "organizasyonlar"
    
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(200), nullable=False)
    musteri_adi = Column(String(200), index=True)
    musteri_adres = Column(Text)
    baslangic_tarihi = Column(DateTime(timezone=True), server_default=func.now())
    bitis_tarihi = Column(DateTime(timezone=True), nullable=True)
    durum = Column(Enum(DurumEnum), default=DurumEnum.DEVAM_EDIYOR)
    notlar = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    
    # İlişkiler
    kalibrasyonlar = relationship("Kalibrasyon", back_populates="organizasyon")


class CihazTanim(Base):
    """Cihaz tanımları - master data"""
    __tablename__ = "cihaz_tanimlari"
    
    id = Column(Integer, primary_key=True, index=True)
    cihaz_kodu = Column(String(50), unique=True, index=True)  # DK-001 gibi
    cihaz_adi = Column(String(100), nullable=False)
    cihaz_tipi = Column(Enum(CihazTipiEnum), index=True)
    marka = Column(String(100))
    model = Column(String(100))
    seri_no = Column(String(100), unique=True, index=True)
    olcme_araligi = Column(String(100))
    cozunurluk = Column(String(50))
    
    # Kalibrasyon için gerekli alanlar (JSON)
    kalibrasyon_noktalari = Column(JSON)  # [0, 25, 50, 75, 100] gibi
    toleranslar = Column(JSON)  # {"sapma": 0.05, "belirsizlik": 0.02} gibi
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # İlişkiler
    kalibrasyonlar = relationship("Kalibrasyon", back_populates="cihaz")


class Kalibrasyon(Base):
    """Tek bir cihazın kalibrasyonu"""
    __tablename__ = "kalibrasyonlar"
    
    id = Column(Integer, primary_key=True, index=True)
    organizasyon_id = Column(Integer, ForeignKey("organizasyonlar.id"))
    cihaz_id = Column(Integer, ForeignKey("cihaz_tanimlari.id"))
    
    # Ortam koşulları
    sicaklik = Column(Float)
    nem = Column(Float)
    
    # Ölçüm verileri (JSON)
    olcum_verileri = Column(JSON)  # Cihaz tipine göre dinamik
    
    # Sonuç
    uygunluk = Column(Boolean, default=True)
    
    # Sesli özet
    sesli_ozet_path = Column(String(500))
    sesli_ozet_text = Column(Text)
    
    # Ekler
    fotograflar = Column(JSON)  # ["foto1.jpg", "foto2.jpg"]
    ekler = Column(JSON)  # ["dokuman1.pdf", "excel1.xlsx"]
    
    # Durum
    durum = Column(Enum(DurumEnum), default=DurumEnum.DEVAM_EDIYOR)
    kalibrasyon_tarihi = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # İlişkiler
    organizasyon = relationship("Organizasyon", back_populates="kalibrasyonlar")
    cihaz = relationship("CihazTanim", back_populates="kalibrasyonlar")


class FormSablonu(Base):
    """Cihaz tiplerine göre form şablonları"""
    __tablename__ = "form_sablonlari"
    
    id = Column(Integer, primary_key=True, index=True)
    cihaz_tipi = Column(Enum(CihazTipiEnum), unique=True)
    form_yapisi = Column(JSON)  # Form field'larının tanımı
    varsayilan_noktalar = Column(JSON)  # Ölçüm noktaları
    hesaplama_kurallari = Column(JSON)  # Sapma, belirsizlik hesaplamaları
