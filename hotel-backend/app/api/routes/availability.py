from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.database.session import get_db
from app.models.booking import Booking
from app.models.room import Room, RoomInventory
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

    if check_out_date <= check_in_date:
        raise HTTPException(
            status_code=422,
            detail="Check-out date must be after check-in date",
        )

    # Check if room exists
    room = db.query(Room).filter(
        Room.room_id == room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    stay_dates = []
    current_date = check_in_date
    while current_date < check_out_date:
        stay_dates.append(current_date)
        current_date += timedelta(days=1)

    inventory_rows = db.query(RoomInventory).filter(
        RoomInventory.room_id == room_id,
        RoomInventory.date.in_(stay_dates),
    ).all()
    inventory_by_date = {item.date: item for item in inventory_rows}

    overlapping_bookings = db.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.status != "CANCELLED",
        Booking.check_in < check_out_date,
        Booking.check_out > check_in_date,
    ).all()

    unavailable_dates = []
    inventory_details = []
    for stay_date in stay_dates:
        inventory = inventory_by_date.get(stay_date)
        booked_rooms = sum(
            1
            for booking in overlapping_bookings
            if booking.check_in <= stay_date < booking.check_out
        )

        if not inventory:
            unavailable_dates.append(format_hotel_date(stay_date))
            inventory_details.append({
                "date": format_hotel_date(stay_date),
                "available_rooms": 0,
                "booked_rooms": booked_rooms,
                "available": False,
            })
            continue

        remaining_rooms = max(inventory.available_rooms - booked_rooms, 0)
        is_available = remaining_rooms > 0
        if not is_available:
            unavailable_dates.append(format_hotel_date(stay_date))
        inventory_details.append({
            "date": format_hotel_date(stay_date),
            "available_rooms": inventory.available_rooms,
            "booked_rooms": booked_rooms,
            "remaining_rooms": remaining_rooms,
            "available": is_available,
        })

    return {
        "room_id": room_id,
        "check_in": format_hotel_date(check_in_date),
        "check_out": format_hotel_date(check_out_date),
        "available": not unavailable_dates,
        "unavailable_dates": unavailable_dates,
        "inventory": inventory_details,
    }