"""
Veritabanı modelleri - Kalibrasyon raporları ve ilişkili veriler
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class KalibrasyonRaporu(Base):
    """Ana kalibrasyon raporu tablosu"""
    __tablename__ = "kalibrasyon_raporlari"
    
    id = Column(Integer, primary_key=True, index=True)
    sertifika_no = Column(String(50), unique=True, index=True, nullable=False)
    
    # Müşteri bilgileri
    musteri_adi = Column(String(200), index=True)
    musteri_adres = Column(Text)
    istek_no = Column(String(50))
    
    # Cihaz bilgileri
    cihaz_tipi = Column(String(100), index=True)
    cihaz_marka = Column(String(100))
    cihaz_model = Column(String(100))
    seri_no = Column(String(100), index=True)
    olcme_araligi = Column(String(100))
    cozunurluk = Column(String(50))
    
    # Kalibrasyon bilgileri
    kalibrasyon_tarihi = Column(DateTime, index=True)
    sicaklik = Column(String(50))
    nem = Column(String(50))
    
    # Dosya yolları
    pdf_path = Column(String(500))
    ses_kaydi_path = Column(String(500))
    gorsel_path = Column(String(500), nullable=True)
    
    # Durum bilgileri
    durum = Column(String(50), default="tamamlandi")  # tamamlandi, iptal, beklemede
    uygunluk = Column(Boolean, default=True)  # Uygun/Uygun değil
    
    # JSON olarak tüm rapor verisi (backup/detaylı veri için)
    rapor_data = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))  # Teknisyen/kullanıcı adı
    
    # İlişkiler
    olcumler = relationship("OlcumSonucu", back_populates="rapor", cascade="all, delete-orphan")
    dosyalar = relationship("RaporDosya", back_populates="rapor", cascade="all, delete-orphan")


class OlcumSonucu(Base):
    """Ölçüm sonuçları detay tablosu"""
    __tablename__ = "olcum_sonuclari"
    
    id = Column(Integer, primary_key=True, index=True)
    rapor_id = Column(Integer, ForeignKey("kalibrasyon_raporlari.id"))
    
    olcum_tipi = Column(String(50))  # dis_cap, ic_cap, derinlik, kademe
    referans_deger = Column(Float)
    olculen_deger = Column(Float)
    sapma = Column(Float)
    belirsizlik = Column(Float)
    
    # Alt ölçümler için (iç, orta, dış)
    alt_tip = Column(String(20), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # İlişki
    rapor = relationship("KalibrasyonRaporu", back_populates="olcumler")


class RaporDosya(Base):
    """Rapora ait dosyalar (PDF, ses, görsel vs.)"""
    __tablename__ = "rapor_dosyalari"
    
    id = Column(Integer, primary_key=True, index=True)
    rapor_id = Column(Integer, ForeignKey("kalibrasyon_raporlari.id"))
    
    dosya_tipi = Column(String(50))  # pdf, audio, image, excel
    dosya_adi = Column(String(200))
    dosya_yolu = Column(String(500))
    dosya_boyutu = Column(Integer)  # bytes
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # İlişki
    rapor = relationship("KalibrasyonRaporu", back_populates="dosyalar")


class Kullanici(Base):
    """Kullanıcı tablosu (ileride eklenecek)"""
    __tablename__ = "kullanicilar"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    ad_soyad = Column(String(200))
    sifre_hash = Column(String(200))
    rol = Column(String(50), default="teknisyen")  # admin, teknisyen, musteri
    aktif = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
