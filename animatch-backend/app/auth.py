from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings

# Initialize security scheme with auto_error=False to prevent FastAPI from raising 403 automatically
security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_minutes: int = 60) -> str:
    """
    Generates a stateless HS256 JSON Web Token (JWT) with an expiration time.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Decodes and validates a JWT token using HS256.
    Raises HTTP 401 if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency that extracts the Bearer token from the Authorization header,
    verifies it, and returns the decoded payload. Always raises HTTP 401 on failure (never 403).
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials are missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return verify_token(credentials.credentials)
