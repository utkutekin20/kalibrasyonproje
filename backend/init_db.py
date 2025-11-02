"""
Veritabanı tablolarını oluşturma script'i
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from database import Base, DATABASE_URL
from models import KalibrasyonRaporu, OlcumSonucu, RaporDosya, Kullanici
from new_models import Organizasyon, CihazTanim, Kalibrasyon, FormSablonu
from standards_models import CalibrasyonStandardi, StandardSablon, SablonParametre

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """Veritabanı tablolarını oluştur"""
    logger.info(f"Veritabanına bağlanılıyor: {DATABASE_URL}")
    
    # Engine oluştur
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Tüm tabloları oluştur
        logger.info("Tablolar oluşturuluyor...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tablolar başarıyla oluşturuldu!")
    
    await engine.dispose()


async def drop_tables():
    """Tüm tabloları sil (dikkatli kullan!)"""
    logger.warning("TÜM TABLOLAR SİLİNECEK!")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Tüm tablolar silindi.")
    
    await engine.dispose()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        # python init_db.py drop - tabloları siler
        asyncio.run(drop_tables())
    else:
        # python init_db.py - tabloları oluşturur
        asyncio.run(init_db())
