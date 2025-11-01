"""
Veritabanı bağlantı ve session yönetimi
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv("production.env")

# PostgreSQL için async connection string
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/kalibrasyon_db"
)

# Async engine oluştur
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # SQL sorgularını logla (development)
    poolclass=NullPool,  # Connection pooling
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base model
Base = declarative_base()

# Dependency injection için
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
