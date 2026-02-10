from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Railway provides DATABASE_URL. 
# Note: SQLAlchemy requires 'postgresql://' but Railway might give 'postgres://'.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fallback for local testing if env var is not set (sqlite)
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./local_payments.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
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
    email = Column(String, nullable=True) # User email if provided
    payment_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
