"""Password hashing, session tokens, and a small login rate limiter."""
import hashlib
import hmac
import os
import time
from collections import defaultdict, deque
from typing import Optional

import jwt

from .config import SECRET_KEY, SESSION_DAYS

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _algo, iters, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


_DUMMY_HASH = hash_password("not-a-real-password")   # used so unknown emails take the same time


def burn_time() -> None:
    verify_password("x", _DUMMY_HASH)


def make_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": int(time.time()) + SESSION_DAYS * 86400}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def read_token(token: str) -> Optional[int]:
    try:
        return int(jwt.decode(token, SECRET_KEY, algorithms=["HS256"])["sub"])
    except Exception:
        return None


class RateLimiter:
    """Max `limit` hits per `window` seconds per key (in memory, fine for one server)."""

    def __init__(self, limit: int, window: int):
        self.limit, self.window = limit, window
        self.hits = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True


login_limiter = RateLimiter(limit=10, window=300)
