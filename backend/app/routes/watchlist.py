from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import User, WatchlistItem, AdjacentMapping
from app.schemas import WatchlistItemCreate, WatchlistItemOut, AdjacentMappingCreate, AdjacentMappingOut
from app.routes.users import get_current_user

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("/", response_model=list[WatchlistItemOut])
def list_watchlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == user.id).order_by(WatchlistItem.added_at.desc())
    ).scalars().all()
    return items


@router.post("/", response_model=WatchlistItemOut, status_code=201)
def add_to_watchlist(
    body: WatchlistItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id,
            WatchlistItem.ticker == body.ticker.upper(),
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Ticker already in watchlist")

    item = WatchlistItem(
        user_id=user.id,
        ticker=body.ticker.upper(),
        company=body.company,
    )
    db.add(item)
    db.flush()

    for adj in body.adjacents:
        mapping = AdjacentMapping(
            watchlist_id=item.id,
            adjacent_ticker=adj.adjacent_ticker.upper(),
            adjacent_company=adj.adjacent_company,
        )
        db.add(mapping)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{watchlist_id}", status_code=204)
def remove_from_watchlist(
    watchlist_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == watchlist_id,
            WatchlistItem.user_id == user.id,
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    db.delete(item)
    db.commit()


# --- Adjacent mapping management ---

@router.post("/{watchlist_id}/adjacents", response_model=AdjacentMappingOut, status_code=201)
def add_adjacent(
    watchlist_id: UUID,
    body: AdjacentMappingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == watchlist_id,
            WatchlistItem.user_id == user.id,
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    existing = db.execute(
        select(AdjacentMapping).where(
            AdjacentMapping.watchlist_id == watchlist_id,
            AdjacentMapping.adjacent_ticker == body.adjacent_ticker.upper(),
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Adjacent ticker already mapped")

    mapping = AdjacentMapping(
        watchlist_id=watchlist_id,
        adjacent_ticker=body.adjacent_ticker.upper(),
        adjacent_company=body.adjacent_company,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


@router.delete("/{watchlist_id}/adjacents/{mapping_id}", status_code=204)
def remove_adjacent(
    watchlist_id: UUID,
    mapping_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == watchlist_id,
            WatchlistItem.user_id == user.id,
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    mapping = db.execute(
        select(AdjacentMapping).where(
            AdjacentMapping.id == mapping_id,
            AdjacentMapping.watchlist_id == watchlist_id,
        )
    ).scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=404, detail="Adjacent mapping not found")

    db.delete(mapping)
    db.commit()
