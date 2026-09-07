from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
import secrets
import string
#Generate 6character a;phanueric booking ID
def generate_booking_id():
    characters = string.ascii_uppercase + string.digits
    return "HLLG" + "".join(
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

    room = relationship("Room")