from datetime import datetime, timedelta
from typing import Optional, Union
import hmac
import hashlib

import structlog

# Optional imports for security packages
try:
    from jose import JWTError, jwt
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False
    jwt = None
    JWTError = Exception

try:
    from passlib.context import CryptContext
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    CryptContext = None

from app.core.config import get_settings

# Set up logger with fallback
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Password hashing context with fallback
if PASSLIB_AVAILABLE:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:
    pwd_context = None


def create_access_token(
    subject: Union[str, int], 
    expires_delta: Optional[timedelta] = None
) -> str:
    if not JOSE_AVAILABLE:
        logger.warning("JWT token creation unavailable - python-jose not installed")
        return ""
        
    settings = get_settings()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    logger.debug("Access token created", subject=subject, expires=expire)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    if not JOSE_AVAILABLE:
        logger.warning("JWT token verification unavailable - python-jose not installed")
        return None
        
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        subject: str = payload.get("sub")
        if subject is None:
            return None
        return subject
    except JWTError as e:
        logger.warning("Token verification failed", error=str(e))
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not PASSLIB_AVAILABLE:
        logger.warning("Password verification unavailable - passlib not installed")
        # Simple fallback comparison (not secure for production)
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    if not PASSLIB_AVAILABLE:
        logger.warning("Password hashing unavailable - passlib not installed")
        # Simple hash as fallback (not secure for production)
        return hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(password)


def generate_webhook_signature(payload: str, secret: str) -> str:
    import hmac
    import hashlib
    
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={signature}"


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    expected_signature = generate_webhook_signature(payload, secret)
    return hmac.compare_digest(signature, expected_signature)
