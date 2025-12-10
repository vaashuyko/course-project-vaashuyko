from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.errors import ApiError
from app.core.security import get_current_user
from app.database import get_db

router = APIRouter(tags=["wishes"])


@router.post(
    "",
    response_model=schemas.WishRead,
    status_code=status.HTTP_201_CREATED,
)
def create_wish(
    wish_in: schemas.WishCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.WishRead:
    wish = models.Wish(
        title=wish_in.title,
        link=wish_in.link,
        price_estimate=wish_in.price_estimate,
        notes=wish_in.notes,
        owner_id=current_user.id,
    )
    db.add(wish)
    db.commit()
    db.refresh(wish)
    return wish


@router.get("", response_model=schemas.WishListResponse)
def list_wishes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    price_lt: Optional[Decimal] = Query(
        None,
        ge=0,
        description="Вернуть желания с ценой строго меньше указанной",
    ),
) -> schemas.WishListResponse:
    query = db.query(models.Wish).filter(models.Wish.owner_id == current_user.id)

    if price_lt is not None:
        query = query.filter(models.Wish.price_estimate < price_lt)

    total = query.with_entities(func.count(models.Wish.id)).scalar() or 0

    items = (
        query.order_by(models.Wish.created_at.desc()).offset(offset).limit(limit).all()
    )

    return schemas.WishListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


def _get_wish_or_error(
    wish_id: int,
    db: Session,
    current_user: models.User,
) -> models.Wish:
    wish = db.get(models.Wish, wish_id)
    if not wish:
        raise ApiError(
            code="wish_not_found",
            message="Wish not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if wish.owner_id != current_user.id:
        raise ApiError(
            code="forbidden",
            message="You do not own this wish",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return wish


@router.get("/{wish_id}", response_model=schemas.WishRead)
def get_wish(
    wish_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.WishRead:
    wish = _get_wish_or_error(wish_id, db, current_user)
    return wish


@router.put("/{wish_id}", response_model=schemas.WishRead)
def update_wish(
    wish_id: int,
    wish_update: schemas.WishUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.WishRead:
    wish = _get_wish_or_error(wish_id, db, current_user)

    data = wish_update.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(wish, field, value)

    db.add(wish)
    db.commit()
    db.refresh(wish)
    return wish


@router.delete("/{wish_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wish(
    wish_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> None:
    wish = _get_wish_or_error(wish_id, db, current_user)
    db.delete(wish)
    db.commit()
