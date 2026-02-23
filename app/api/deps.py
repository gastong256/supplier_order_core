from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# ── Type aliases (inject with Annotated for clean signatures) ─────────────────

DBSession = Annotated[AsyncSession, Depends(get_db)]
Token = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user_id(token: Token) -> str:
    """Validate JWT and return the subject (user ID) as a string."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exc
        return user_id
    except JWTError:
        raise credentials_exc


CurrentUserID = Annotated[str, Depends(get_current_user_id)]
