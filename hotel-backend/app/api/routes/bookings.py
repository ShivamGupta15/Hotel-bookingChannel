from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.booking import Booking
from app.models.coupon import Coupon
from app.models.room import Room, RoomInventory
from app.schemas.booking import BookingCreate, BookingFoundResponse, BookingResponse
from app.services.payment_service import PaymentService


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

    if booking_data.check_in >= booking_data.check_out:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date"
        )

    stay_dates = []
    current_date = booking_data.check_in
    while current_date < booking_data.check_out:
        stay_dates.append(current_date)
        current_date += timedelta(days=1)

    inventory_rows = db.query(RoomInventory).filter(
        RoomInventory.room_id == booking_data.room_id,
        RoomInventory.date.in_(stay_dates),
    ).all()
    inventory_by_date = {item.date: item for item in inventory_rows}
    overlapping_bookings = db.query(Booking).filter(
        Booking.room_id == booking_data.room_id,
        Booking.status != "CANCELLED",
        Booking.check_in < booking_data.check_out,
        Booking.check_out > booking_data.check_in,
    ).all()

    for stay_date in stay_dates:
        inventory = inventory_by_date.get(stay_date)
        if not inventory:
            raise HTTPException(
                status_code=409,
                detail=f"Room inventory is not configured for {stay_date.strftime('%d-%m-%Y')}",
            )

        booked_rooms = sum(
            1
            for existing_booking in overlapping_bookings
            if existing_booking.check_in <= stay_date < existing_booking.check_out
        )
        if booked_rooms >= inventory.available_rooms:
            raise HTTPException(
                status_code=409,
                detail="Room is not available for these dates",
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

    subtotal_amount = Decimal(room.price_per_night * len(stay_dates))
    discount_amount = Decimal("0.00")
    coupon = None
    if booking_data.coupon_code:
        coupon = db.query(Coupon).filter(
            Coupon.code == booking_data.coupon_code.strip().upper(),
            Coupon.is_active.is_(True),
        ).first()
        today = date.today()
        if not coupon or (
            coupon.valid_from and today < coupon.valid_from
        ) or (
            coupon.valid_until and today > coupon.valid_until
        ) or (
            coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit
        ):
            raise HTTPException(status_code=400, detail="Invalid or expired coupon")

        if coupon.discount_type == "PERCENTAGE":
            discount_amount = subtotal_amount * coupon.discount_value / Decimal("100")
            if coupon.max_discount is not None:
                discount_amount = min(discount_amount, coupon.max_discount)
        else:
            discount_amount = coupon.discount_value
        discount_amount = min(discount_amount, subtotal_amount)

    total_amount = subtotal_amount - discount_amount

    # Create booking
    booking = Booking(
        room_id=booking_data.room_id,
        guest_name=booking_data.guest_name,
        email=booking_data.email,
        phone=booking_data.phone,
        check_in=booking_data.check_in,
        check_out=booking_data.check_out,
        guests=booking_data.guests,
        coupon_code=coupon.code if coupon else None,
        subtotal_amount=subtotal_amount,
        discount_amount=discount_amount,
        total_amount=total_amount,
    )

    if coupon:
        coupon.used_count += 1

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

    booking = PaymentService(db).cancel_booking_with_refund(booking_id)
    booking.admin_activity = f"Customer cancelled booking at {datetime.utcnow().isoformat()}Z"
    db.commit()
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