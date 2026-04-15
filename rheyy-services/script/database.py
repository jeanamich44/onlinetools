import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# ==============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL:
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./rheyy_services.db"

# ==============================================================================

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

from sqlalchemy.orm import relationship

# ==============================================================================

class Reseller(Base):
    __tablename__ = "resellers"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    balance = Column(Float, default=0.0)
    categories = Column(Text, default="")
    role = Column(String, default="standard")
    total_purchases = Column(Integer, default=0)
    total_payment_requests = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    transactions = relationship("Transaction", back_populates="reseller")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    reseller_id = Column(Integer, ForeignKey("resellers.id"))
    amount = Column(Float)
    type = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="completed")
    reseller = relationship("Reseller", back_populates="transactions")

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Payment(Base):
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

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String)

# ==============================================================================

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
