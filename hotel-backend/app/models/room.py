from sqlalchemy import UniqueConstraint, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Date
from app.schemas.date import HotelDate
from app.database.base import Base
from datetime import date


class Room(Base):
    __tablename__ = "rooms"

    room_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    price_per_night: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

class RoomInventory(Base):
    __tablename__ = "room_inventory"

    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "date",
            name="uq_room_inventory_room_date"
        ),
    )

    inventory_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.room_id"),
        nullable=False,
        index=True
    )

    date: Mapped[HotelDate] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    available_rooms: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )