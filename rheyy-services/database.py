import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL de la base de données (PostgreSQL sur Railway)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL:
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # Fallback pour le développement local si nécessaire
    SQLALCHEMY_DATABASE_URL = "sqlite:///./rheyy_services.db"
    logger.warning("DATABASE_URL non trouvée, utilisation d'une base SQLite locale.")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# =========================
# MODÈLES
# =========================

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Payment(Base):
    """Miroir de la table de l'API principale pour la lecture."""
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    checkout_id = Column(String, index=True, nullable=True)
    checkout_ref = Column(String, unique=True, index=True)
    amount = Column(Float)
    currency = Column(String, default="EUR")
    status = Column(String, default="PENDING")
    ip_address = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    user_data = Column(String, nullable=True)
    is_generated = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# =========================
# INITIALISATION
# =========================

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
