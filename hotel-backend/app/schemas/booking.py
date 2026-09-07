from decimal import Decimal

from pydantic import BaseModel, EmailStr, ConfigDict, Field

from app.schemas.date import HotelDate


class BookingCreate(BaseModel):
    room_id: int
    guest_name: str
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    check_in: HotelDate = Field(..., description="Check-in date in dd-mm-yyyy format")
    check_out: HotelDate = Field(..., description="Check-out date in dd-mm-yyyy format")
    guests: int = Field(..., ge=1, description="Number of guests, must be at least 1")
    coupon_code: str | None = Field(default=None, max_length=50)


class BookingResponse(BookingCreate):
    booking_id: str
    status: str
    admin_activity: str | None = None
    subtotal_amount: Decimal | None = None
    discount_amount: Decimal | None = None
    total_amount: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)
class BookingFoundResponse(BookingResponse):
    pass