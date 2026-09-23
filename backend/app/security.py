import hashlib
import hmac
import secrets
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .db import get_db
from .models import Company, LoginSession, Member, now


def hash_password(password):
    salt = secrets.token_hex(16)
    value = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), 310000
    ).hex()
    return f"pbkdf2_sha256$310000${salt}${value}"


def verify_password(password, encoded):
    try:
        _, rounds, salt, expected = encoded.split("$")
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), int(rounds)
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def current_member(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("estimate2_session", "")
    session = db.get(LoginSession, token_hash(token)) if token else None
    if not session or session.expires_at <= now():
        raise HTTPException(401, "ログインしてください。")
    member = db.get(Member, session.membership_id)
    if not member or not member.active or not db.get(Company, member.company_id).active:
        raise HTTPException(401, "このアカウントは現在利用できません。")
    return member


def require_admin(member):
    if member.role != "admin":
        raise HTTPException(403, "会社管理者のみ操作できます。")
