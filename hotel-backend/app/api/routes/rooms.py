from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.database.session import get_db
from app.models.room import Room
from app.schemas.room import RoomCreate, RoomResponse
from app.security import require_admin

router = APIRouter(
    prefix="/api/v1/rooms",
    tags=["Rooms"]
)


@router.get("/", response_model=list[RoomResponse])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()


@router.post("/", response_model=RoomResponse)
def create_room(
    room: RoomCreate,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    new_room = Room(
        name=room.name,
        description=room.description,
        price_per_night=room.price_per_night,
        capacity=room.capacity,
        image_url=room.image_url
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return new_room

@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: int,
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.room_id == room_id).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    return room

@router.put("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_data: RoomCreate,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    room.name = room_data.name
    room.description = room_data.description
    room.price_per_night = room_data.price_per_night
    room.capacity = room_data.capacity
    room.image_url = room_data.image_url

    db.commit()
    db.refresh(room)

    return room

@router.delete("/{room_id}")
def delete_room(
    room_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.room_id == room_id).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    db.delete(room)
    db.commit()

    return {
        "message": "Room deleted successfully"
    }