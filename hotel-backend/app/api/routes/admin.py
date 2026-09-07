from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.room import Room, RoomInventory
from app.models.booking import Booking
from app.models.coupon import Coupon
from app.models.payment import Payment
from app.schemas.admin import (
    AdminLoginRequest,
    AdminTokenResponse,
    BulkInventoryUpdateRequest,
    BulkInventoryUpdateResponse,
)
from app.schemas.room import (
    RoomInventoryCreate,
    RoomInventoryResponse,
    RoomInventoryUpdate,
)
from app.schemas.coupon import CouponCreate, CouponResponse
from app.security import authenticate_admin, create_access_token, require_admin
from app.services.payment_service import PaymentService


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


@router.post("/coupons", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    coupon_data: CouponCreate,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    code = coupon_data.code.strip().upper()
    if coupon_data.valid_until and coupon_data.valid_from and coupon_data.valid_until < coupon_data.valid_from:
        raise HTTPException(status_code=422, detail="Coupon end date must be after start date")
    if coupon_data.discount_type == "PERCENTAGE" and coupon_data.discount_value > 100:
        raise HTTPException(status_code=422, detail="Percentage discount cannot exceed 100")
    if db.query(Coupon).filter(Coupon.code == code).first():
        raise HTTPException(status_code=409, detail="Coupon code already exists")
    coupon = Coupon(
        code=code,
        discount_type=coupon_data.discount_type,
        discount_value=coupon_data.discount_value,
        max_discount=coupon_data.max_discount,
        valid_from=coupon_data.valid_from,
        valid_until=coupon_data.valid_until,
        usage_limit=coupon_data.usage_limit,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.get("/coupons", response_model=list[CouponResponse])
def list_coupons(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


@router.put("/bookings/{booking_id}/cancel", response_model=dict)
def admin_cancel_booking(
    booking_id: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    booking = PaymentService(db).cancel_booking(booking_id)
    booking.admin_activity = f"Admin cancelled booking at {datetime.utcnow().isoformat()}Z"
    db.commit()
    return {
        "booking_id": booking.booking_id,
        "status": booking.status,
    }


@router.get("/bookings", response_model=list[dict])
def admin_list_bookings(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    bookings = db.query(Booking).order_by(Booking.check_in.desc()).all()
    result = []
    for booking in bookings:
        payment = db.query(Payment).filter(
            Payment.booking_id == booking.booking_id
        ).order_by(Payment.payment_id.desc()).first()
        result.append({
            "booking_id": booking.booking_id,
            "room_id": booking.room_id,
            "guest_name": booking.guest_name,
            "phone": booking.phone,
            "email": booking.email,
            "check_in": booking.check_in.strftime("%d-%m-%Y"),
            "check_out": booking.check_out.strftime("%d-%m-%Y"),
            "booking_status": booking.status,
            "admin_activity": booking.admin_activity,
            "coupon_code": booking.coupon_code,
            "subtotal_amount": str(booking.subtotal_amount) if booking.subtotal_amount is not None else None,
            "discount_amount": str(booking.discount_amount) if booking.discount_amount is not None else "0.00",
            "total_amount": str(booking.total_amount) if booking.total_amount is not None else None,
            "payment_status": payment.status if payment else None,
            "payment_amount": str(payment.amount) if payment else None,
            "razorpay_order_id": payment.provider_order_id if payment else None,
            "razorpay_payment_id": payment.provider_payment_id if payment else None,
            "razorpay_signature": payment.provider_signature if payment else None,
            "provider_refund_id": payment.provider_refund_id if payment else None,
            "refunded_amount": str(payment.refunded_amount) if payment else "0.00",
        })
    return result


@router.put("/bookings/{booking_id}/confirm", response_model=dict)
def admin_confirm_booking(
    booking_id: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == "CANCELLED":
        raise HTTPException(status_code=409, detail="Cancelled booking cannot be confirmed")
    booking.status = "CONFIRMED"
    booking.admin_activity = f"Admin confirmed booking at {datetime.utcnow().isoformat()}Z"
    db.commit()
    return {"booking_id": booking.booking_id, "status": booking.status}


@router.put("/bookings/{booking_id}/refund", response_model=dict)
def admin_refund_booking(
    booking_id: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    booking = PaymentService(db).refund_booking(booking_id)
    booking.admin_activity = f"Admin refunded booking at {datetime.utcnow().isoformat()}Z"
    db.commit()
    return {"booking_id": booking.booking_id, "status": booking.status}


@router.post(
    "/inventory/bulk",
    response_model=BulkInventoryUpdateResponse,
)
def bulk_update_inventory(
    inventory: BulkInventoryUpdateRequest,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.room_id == inventory.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    dates = list(dict.fromkeys(inventory.dates))
    existing_inventory = db.query(RoomInventory).filter(
        RoomInventory.room_id == inventory.room_id,
        RoomInventory.date.in_(dates),
    ).all()
    existing_by_date = {item.date: item for item in existing_inventory}

    created_count = 0
    updated_count = 0
    for selected_date in dates:
        item = existing_by_date.get(selected_date)
        if item:
            item.available_rooms = inventory.available_rooms
            updated_count += 1
        else:
            db.add(RoomInventory(
                room_id=inventory.room_id,
                date=selected_date,
                available_rooms=inventory.available_rooms,
            ))
            created_count += 1

    db.commit()

    return BulkInventoryUpdateResponse(
        room_id=inventory.room_id,
        dates=dates,
        available_rooms=inventory.available_rooms,
        created_count=created_count,
        updated_count=updated_count,
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