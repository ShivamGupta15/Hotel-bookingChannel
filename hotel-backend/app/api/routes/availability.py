import os

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.database.session import get_db
from app.models.booking import Booking
from app.models.room import Room
from app.schemas.date import format_hotel_date, parse_hotel_date

router = APIRouter(
    prefix="/api/v1/availability",
    tags=["Availability"]
)

@router.get("/", description="Enter dates in dd-mm-yyyy format")
def check_availability(
    room_id: int,
    check_in: str = Query(...,
        description="Check-in date. Enter in dd-mm-yyyy format",
        examples=date.today().strftime("%d-%m-%Y")),
    check_out: str = Query(...,
        description="Check-out date. Enter in dd-mm-yyyy format",
        examples=(date.today() + timedelta(days=1)).strftime("%d-%m-%Y")),
    db: Session = Depends(get_db)
):
    try:
        check_in_date = parse_hotel_date(check_in)
        check_out_date = parse_hotel_date(check_out)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    # Check if room exists
    room = db.query(Room).filter(
        Room.room_id == room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    # Check for overlapping booking
    existing_booking = db.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.status != "CANCELLED",
        Booking.check_in < check_out_date,
        Booking.check_out > check_in_date
    ).first()

    if existing_booking:
        return {
            "room_id": room_id,
            "check_in": format_hotel_date(check_in_date),
            "check_out": format_hotel_date(check_out_date),
            "available": False
        }

    return {
        "room_id": room_id,
        "check_in": format_hotel_date(check_in_date),
        "check_out": format_hotel_date(check_out_date),
        "available": True
    }