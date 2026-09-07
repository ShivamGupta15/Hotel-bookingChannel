from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
import secrets
import string
#Generate 6character a;phanueric booking ID
def generate_booking_id():
    characters = string.ascii_uppercase + string.digits
    return "TEST" + "".join(
        secrets.choice(characters)
        for _ in range(6)
    )


class Booking(Base):
    __tablename__ = "bookings"

    booking_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        default=generate_booking_id,
        index=True
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.room_id"),
        nullable=False
    )

    guest_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    check_in: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    check_out: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    guests: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False
    )

    admin_activity: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    coupon_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subtotal_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    room = relationship("Room")