import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import hashlib
import base64
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()
from systeme.database import get_db, Reseller

# =========================
# CONFIGURATION
# =========================

SECRET_KEY = os.getenv("RHEYY_TOKEN_KEY", "rheyy-super-token-key-change-it")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120


ALLOWED_IPS = [ip.strip() for ip in os.getenv("ADMIN_IP_WHITELIST", "127.0.0.1").split(",")]
ENABLE_IP_WHITELIST = os.getenv("ENABLE_IP_WHITELIST", "false").lower() == "true"

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()

# =========================
# UTILITAIRES MOT DE PASSE
# =========================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# =========================
# GESTION JWT
# =========================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# =========================
# DÉPENDANCES DE SÉCURITÉ
# =========================

def check_ip_whitelist(request: Request):
    if not ENABLE_IP_WHITELIST:
        return True
        
    client_ip = request.headers.get("x-forwarded-for", request.client.host)
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
        
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(
            status_code=403, 
            detail="Accès refusé : IP non autorisée."
        )
    return client_ip

async def get_current_admin(
    request: Request,
    auth: HTTPAuthorizationCredentials = Security(security)
):
    check_ip_whitelist(request)
    
    token = auth.credentials
    credentials_exception = HTTPException(
        status_code=401,
        detail="Session invalide ou expirée",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    return username

async def get_current_reseller(
    auth: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    token = auth.credentials
    credentials_exception = HTTPException(
        status_code=401,
        detail="Session revendeur invalide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    reseller = db.query(Reseller).filter(Reseller.username == username).first()

    if reseller is None or not reseller.is_active:
        raise credentials_exception
        
    return reseller
