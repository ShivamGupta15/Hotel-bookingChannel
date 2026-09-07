from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Payment(Base):
    __tablename__ = "payments"

    __table_args__ = (
        UniqueConstraint(
            "provider_payment_id",
            name="uq_payments_provider_payment_id",
        ),
        UniqueConstraint(
            "idempotency_key",
            name="uq_payments_idempotency_key",
        ),
    )

    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[str] = mapped_column(
        ForeignKey("bookings.booking_id"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False, default="razorpay")
    provider_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_refund_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    refunded_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    booking = relationship("Booking")
