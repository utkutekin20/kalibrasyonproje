"""
Veritabanı bağlantısını test et
"""
import asyncio
from database import DATABASE_URL, get_db
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def test_connection():
    """PostgreSQL bağlantısını test et"""
    print(f"Bağlantı test ediliyor: {DATABASE_URL}")
    
    try:
        # Engine oluştur
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        # Bağlantıyı test et
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ PostgreSQL bağlantısı başarılı!")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Bağlantı hatası: {str(e)}")
        print("\nKontrol listesi:")
        print("1. Docker container çalışıyor mu? (docker ps)")
        print("2. Port 5432 açık mı?")
        print("3. production.env'de DATABASE_URL doğru mu?")


if __name__ == "__main__":
    asyncio.run(test_connection())
