"""Password hashing utilities.

INTENTIONAL VULNERABILITY #5: Weak Password Storage.
Passwords are hashed with unsalted MD5 (`hashlib.md5`). There is deliberately
no salt, no pepper, and no key derivation function, so the digests are
reversible with rainbow tables. Do NOT "fix" this — it is a lab learning
target (see docs/TDD.md section 3.1.5).
"""

import hashlib


def hash_password(password: str) -> str:
    """Return the unsalted MD5 hexdigest of the given password."""
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Compare a plain password against a stored MD5 hexdigest."""
    return hash_password(plain) == hashed