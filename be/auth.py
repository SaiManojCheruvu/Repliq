from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from jose import jwt
import bcrypt
import os
from datetime import datetime, timedelta, timezone

from database import get_db
from models import User, Business
from schemas import RegisterRequest, LoginRequest, AuthResponse
from logger import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("repliq.auth")

JWT_SECRET = os.getenv("JWT_SECRET", "45640e2dd83973c39e85e19eef8d22394361b25004f33ad45131bd01378f1a66")
ALGORITHM = "HS256"
EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", 8))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(email: str, business_id: str) -> str:
    payload = {
        "sub": email,
        "business_id": business_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    logger.info("Register attempt: %s", body.email)

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        logger.warning("Registration failed - email already exists: %s", body.email)
        raise HTTPException(status_code=400, detail="Email already registered")

    business = Business(
        name=body.business_name,
        agent_name=body.agent_name or "Agent"
    )
    db.add(business)
    db.flush()

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        business_id=business.id
    )
    db.add(user)
    db.commit()

    logger.info("User registered successfully: %s | business: %s", body.email, business.id)
    token = create_token(user.email, business.id)
    return AuthResponse(token=token, business_id=business.id, email=body.email)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    logger.info("Login attempt: %s", body.email)

    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        logger.warning("Login failed - invalid credentials: %s", body.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    logger.info("Login successful: %s", body.email)
    token = create_token(user.email, user.business_id)
    return AuthResponse(token=token, business_id=user.business_id, email=user.email)