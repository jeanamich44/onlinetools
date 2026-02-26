import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# =========================
# CONFIGURATION
# =========================

SECRET_KEY = os.getenv("RHEYY_TOKEN_KEY", "rheyy-super-token-key-change-it")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# Whitelist IP chargée depuis les variables d'environnement (séparées par des virgules)
ALLOWED_IPS = os.getenv("ADMIN_IP_WHITELIST", "127.0.0.1").split(",")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# =========================
# UTILITAIRES MOT DE PASSE
# =========================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Bcrypt a une limite de 72 octets. On s'assure que c'est bien de l'UTF-8
    # et on tronque si nécessaire pour éviter l'erreur 500.
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes.decode('utf-8'))

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
    """Vérifie si l'IP de la requête est autorisée."""
    client_ip = request.headers.get("x-forwarded-for", request.client.host)
    # Gérer les listes d'IP si derrière un proxy (prendre la première)
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
        
    if client_ip not in ALLOWED_IPS:
        # En production, on peut loguer cette tentative
        raise HTTPException(
            status_code=403, 
            detail="Accès refusé : IP non autorisée."
        )
    return client_ip

async def get_current_admin(
    request: Request,
    auth: HTTPAuthorizationCredentials = Security(security)
):
    """Vérifie l'IP ET le token JWT."""
    # 1. Vérifie l'IP
    check_ip_whitelist(request)
    
    # 2. Vérifie le Token
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
