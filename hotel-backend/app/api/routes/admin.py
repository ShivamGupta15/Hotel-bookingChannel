from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.room import Room, RoomInventory
from app.schemas.admin import AdminLoginRequest, AdminTokenResponse
from app.schemas.room import (
    RoomInventoryCreate,
    RoomInventoryResponse,
    RoomInventoryUpdate,
)
from app.security import authenticate_admin, create_access_token, require_admin


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.post("/login", response_model=AdminTokenResponse)
def admin_login(credentials: AdminLoginRequest):
    if not authenticate_admin(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_in = create_access_token()
    return AdminTokenResponse(
        access_token=access_token,
        expires_in=expires_in,
    )


@router.post(
    "/inventory",
    response_model=RoomInventoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_inventory(
    inventory: RoomInventoryCreate,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # Check that the room exists
    room = db.query(Room).filter(
        Room.room_id == inventory.room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    # Check if inventory already exists for this room and date
    existing_inventory = db.query(RoomInventory).filter(
        RoomInventory.room_id == inventory.room_id,
        RoomInventory.date == inventory.date
    ).first()

    if existing_inventory:
        raise HTTPException(
            status_code=400,
            detail="Inventory already exists for this room and date"
        )

    # Create inventory
    new_inventory = RoomInventory(
        room_id=inventory.room_id,
        date=inventory.date,
        available_rooms=inventory.available_rooms
    )

    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)

    return new_inventory


@router.put(
    "/inventory/{inventory_id}",
    response_model=RoomInventoryResponse,
)
def update_inventory(
    inventory_id: int,
    inventory: RoomInventoryUpdate,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing_inventory = db.query(RoomInventory).filter(
        RoomInventory.inventory_id == inventory_id
    ).first()

    if not existing_inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found",
        )

    existing_inventory.available_rooms = inventory.available_rooms
    db.commit()
    db.refresh(existing_inventory)

    return existing_inventory

@router.get("/inventory/{inventory_id}", response_model=RoomInventoryResponse)
def get_inventory(
    inventory_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    inventory = db.query(RoomInventory).filter(
        RoomInventory.inventory_id == inventory_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found",
        )

    return inventory