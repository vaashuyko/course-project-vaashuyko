from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.errors import ApiError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
) -> schemas.UserRead:
    existing = (
        db.query(models.User)
        .filter(
            or_(
                models.User.email == user_in.email,
                models.User.username == user_in.username,
            )
        )
        .first()
    )
    if existing:
        raise ApiError(
            code="user_exists",
            message="User with this email or username already exists",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = models.User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> schemas.Token:
    user = (
        db.query(models.User)
        .filter(
            or_(
                models.User.email == form_data.username,
                models.User.username == form_data.username,
            )
        )
        .first()
    )

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise ApiError(
            code="invalid_credentials",
            message="Incorrect username or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    access_token = create_access_token(subject=user.id)
    return schemas.Token(access_token=access_token)
