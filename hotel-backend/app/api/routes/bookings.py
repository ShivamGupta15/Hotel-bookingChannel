from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.booking import Booking
from app.models.room import Room
from app.schemas.booking import BookingCreate, BookingFoundResponse, BookingResponse


router = APIRouter(
    prefix="/api/v1/bookings",
    tags=["Bookings"]
)

#To make new booking--------------------------------------
@router.post("/", response_model=BookingResponse)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db)
):
    # Check if room exists
    room = db.query(Room).filter(
        Room.room_id == booking_data.room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    # Check for overlapping booking
    existing_booking = db.query(Booking).filter(
        Booking.room_id == booking_data.room_id,
        Booking.status != "CANCELLED",
        Booking.check_in < booking_data.check_out,
        Booking.check_out > booking_data.check_in
    ).first()

    if existing_booking:
        raise HTTPException(
            status_code=409,
            detail="Room is not available for these dates"
        )
    if booking_data.check_in > booking_data.check_out:
        raise HTTPException(
        status_code=400,
        detail="Check-out date must be after check-in date"
    )

    if booking_data.guests <= 0:
        raise HTTPException(
            status_code=400,
            detail="Number of guests must be at least 1"
        )

    if booking_data.guests > room.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"This room can accommodate a maximum of {room.capacity} guests"
        )

    # Create booking
    booking = Booking(
        room_id=booking_data.room_id,
        guest_name=booking_data.guest_name,
        email=booking_data.email,
        phone=booking_data.phone,
        check_in=booking_data.check_in,
        check_out=booking_data.check_out,
        guests=booking_data.guests
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return booking
#to retrieve Booking detail by booking id--------------------------------
@router.get("/{booking_id}", response_model=BookingFoundResponse)
def get_booking(
    booking_id: str = Path(..., description="Alphanumeric Booking ID, for example HLLG2344", min_length=6),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(
        Booking.booking_id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    return booking

@router.put("/{booking_id}/cancel", response_model=BookingFoundResponse)
def cancel_booking(
    booking_id: str = Path(..., description="Alphanumeric Booking ID, for example HLLG2344", min_length=6),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(
        Booking.booking_id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if booking.status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Booking is already cancelled"
        )

    booking.status = "CANCELLED"
    db.commit()
    db.refresh(booking)

    return booking

#To confirm the booking-------------------------
@router.post(
    "/{booking_id}/confirm",
    response_model=BookingResponse,
    summary="Confirm a booking",
    description="Confirm a pending hotel booking."
)
def confirm_booking(
    booking_id: str,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(
        Booking.booking_id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if booking.status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Cancelled booking cannot be confirmed"
        )

    if booking.status == "CONFIRMED":
        raise HTTPException(
            status_code=400,
            detail="Booking is already confirmed"
        )

    if booking.status == "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Completed booking cannot be confirmed"
        )

    booking.status = "CONFIRMED"

    db.commit()
    db.refresh(booking)

    return booking

#to mark booking "COMPLETED"--------------------
@router.post(
    "/{booking_id}/complete",
    response_model=BookingResponse,
    summary="Complete a booking",
    description="Mark a confirmed booking as completed."
)
def complete_booking(
    booking_id: str,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(
        Booking.booking_id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if booking.status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Cancelled booking cannot be completed"
        )

    if booking.status == "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Booking must be confirmed before completion"
        )

    if booking.status == "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Booking is already completed"
        )
    if booking.status == "CONFIRMED" and booking.check_out > date.today():
        # Additional logic can be added here if needed
        raise HTTPException(
            status_code=400,
            detail="Booking must be checked in before completion. Current status: " + booking.status
        )

    booking.status = "COMPLETED"

    db.commit()
    db.refresh(booking)

    return booking