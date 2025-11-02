"""
Kalibrasyon standartları ve şablonları için veritabanı modelleri
"""
from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class CalibrasyonStandardi(Base):
    """Kalibrasyon standartları (ISO 17662, EURAMET vb.)"""
    __tablename__ = "kalibrasyon_standartlari"
    
    id = Column(Integer, primary_key=True, index=True)
    kod = Column(String(50), unique=True, index=True, nullable=False)  # ISO 17662:2016
    ad_en = Column(String(200))
    ad_tr = Column(String(200))
    organizasyon = Column(String(50))  # ISO, EURAMET, TURKAK
    yil = Column(Integer)
    aciklama = Column(Text)
    
    # Varsayılan değerler
    varsayilan_kalibrasyon_suresi_ay = Column(Integer, default=12)
    varsayilan_sicaklik_min = Column(Float, default=18.0)
    varsayilan_sicaklik_max = Column(Float, default=28.0)
    varsayilan_nem_min = Column(Float, default=30.0)
    varsayilan_nem_max = Column(Float, default=70.0)
    
    # İlişkiler
    sablonlar = relationship("StandardSablon", back_populates="standart")


class StandardSablon(Base):
    """Her standart için cihaz tipi şablonları"""
    __tablename__ = "standard_sablonlari"
    
    id = Column(Integer, primary_key=True, index=True)
    standart_id = Column(Integer, ForeignKey("kalibrasyon_standartlari.id"))
    
    cihaz_tipi_kodu = Column(String(50), index=True)  # mig_mag_welding, terazi vb.
    cihaz_tipi_adi = Column(String(100))
    grup = Column(String(100))  # Group 1 - Arc Welding
    referans = Column(Text)  # Madde 5.3, Tablo 9-12
    
    kalibrasyon_suresi_ay = Column(Integer, default=12)
    
    # İlişkiler
    standart = relationship("CalibrasyonStandardi", back_populates="sablonlar")
    parametreler = relationship("SablonParametre", back_populates="sablon")


class SablonParametre(Base):
    """Şablon parametreleri (akım, voltaj, test noktaları)"""
    __tablename__ = "sablon_parametreleri"
    
    id = Column(Integer, primary_key=True, index=True)
    sablon_id = Column(Integer, ForeignKey("standard_sablonlari.id"))
    
    parametre_adi = Column(String(100), nullable=False)
    parametre_kodu = Column(String(50), index=True)  # welding_current
    birim = Column(String(20))  # A, V, L/min
    
    # Tolerans bilgileri
    tolerans_tipi = Column(String(20))  # percentage, absolute
    tolerans_degeri = Column(Float)  # 2.0 (%)
    
    # Test noktaları
    test_noktalari = Column(JSON)  # [50, 100, 150, 200, 250, 300]
    
    # Zorunluluk
    zorunlu = Column(Boolean, default=True)
    referans = Column(String(200))  # Madde 5.3
    
    # İlişkiler
    sablon = relationship("StandardSablon", back_populates="parametreler")
