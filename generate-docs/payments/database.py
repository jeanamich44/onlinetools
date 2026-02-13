from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

import logging

# Configure logging to console (stdout) which Railway captures
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway provides DATABASE_URL. 
# Note: SQLAlchemy requires 'postgresql://' but Railway might give 'postgres://'.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL:
    logger.info(f"✅ Found DATABASE_URL: {SQLALCHEMY_DATABASE_URL[:15]}...")
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    logger.error("❌ DATABASE_URL is NOT set! Cannot connect to PostgreSQL.")
    available_keys = list(os.environ.keys())
    raise ValueError(f"DATABASE_URL environment variable is missing! Available keys: {available_keys}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,          # Plus petit pour Railway
    max_overflow=10,      # Limite le débordement
    pool_recycle=300,     # Recycle les connexions toutes les 5 min
    connect_args={"connect_timeout": 10}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    checkout_id = Column(String, index=True, nullable=True) # SumUp Checkout ID
    checkout_ref = Column(String, unique=True, index=True) # Our internal reference (UUID)
    amount = Column(Float)
    currency = Column(String, default="EUR")
    status = Column(String, default="PENDING") # PENDING, PAID, FAILED
    ip_address = Column(String, nullable=True) # User IP
    product_name = Column(String, nullable=True) # e.g. "lbp", "sg", "assurance"
    payment_url = Column(String, nullable=True)
    user_data = Column(String, nullable=True) # JSON store for PDF fields
    is_generated = Column(Integer, default=0) # 0 = No, 1 = Yes (Anti-fraud lock)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
