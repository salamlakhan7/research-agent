import time

import bcrypt
import jwt
from fastapi import Request

from app.config import JWT_SECRET
from app.db import get_conn

ALGO = "HS256"
TOKEN_TTL = 60 * 60 * 24 * 7   # 7 days


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def make_token(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id), "exp": int(time.time()) + TOKEN_TTL}, JWT_SECRET, algorithm=ALGO)


def current_user(request: Request):
    """Returns the user row from the cookie, or None."""
    token = request.cookies.get("token")
    if not token:
        return None
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[ALGO])
    except jwt.PyJWTError:
        return None
    with get_conn() as c:
        return c.execute("SELECT id, name, email FROM users WHERE id=?", (int(data["sub"]),)).fetchone()