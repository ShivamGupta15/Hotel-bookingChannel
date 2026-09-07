from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.integrations.razorpay_client import RazorpayClient
from app.models.booking import Booking
from app.models.payment import Payment
from app.schemas.payment import PaymentOrderCreate, PaymentVerifyRequest


class PaymentService:
    def __init__(self, db: Session, razorpay_client: RazorpayClient | None = None):
        self.db = db
        self.razorpay = razorpay_client or RazorpayClient()

    def create_order(self, request: PaymentOrderCreate) -> Payment:
        booking = self.db.query(Booking).filter(
            Booking.booking_id == request.booking_id
        ).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.status in {"CONFIRMED", "COMPLETED"}:
            raise HTTPException(status_code=409, detail="Booking is already paid")

        existing = self.db.query(Payment).filter(
            Payment.idempotency_key == request.idempotency_key
        ).first()
        if existing:
            return existing

        amount_paise = (
            int((booking.total_amount * 100).quantize(Decimal("1")))
            if booking.total_amount is not None
            else request.amount_paise
        )
        provider_order = self.razorpay.create_order(
            amount=amount_paise,
            currency=request.currency.upper(),
            receipt=request.booking_id,
        )
        payment = Payment(
            booking_id=booking.booking_id,
            provider_order_id=provider_order["id"],
            idempotency_key=request.idempotency_key,
            amount=booking.total_amount
            if booking.total_amount is not None
            else Decimal(request.amount_paise) / Decimal(100),
            currency=request.currency.upper(),
            status="PENDING",
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def verify_payment(self, request: PaymentVerifyRequest) -> Payment:
        payment = self.db.query(Payment).filter(
            Payment.payment_id == request.payment_id
        ).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        if payment.provider_order_id != request.razorpay_order_id:
            raise HTTPException(status_code=400, detail="Payment order mismatch")

        try:
            self.razorpay.verify_payment_signature(
                request.razorpay_order_id,
                request.razorpay_payment_id,
                request.razorpay_signature,
            )
        except Exception as error:
            self._mark_failed(payment, "Invalid payment signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment signature",
            ) from error

        self._mark_captured(payment, request.razorpay_payment_id)
        payment.provider_signature = request.razorpay_signature
        self.db.commit()
        return payment

    def process_webhook(self, event: dict) -> None:
        event_name = event.get("event")
        payload = event.get("payload", {})
        payment_entity = payload.get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")
        if not order_id or not payment_id:
            return

        payment = self.db.query(Payment).filter(
            Payment.provider_order_id == order_id
        ).first()
        if not payment:
            return

        if event_name == "payment.captured":
            self._mark_captured(payment, payment_id, payment_entity.get("method"))
        elif event_name == "payment.failed":
            self._mark_failed(
                payment,
                payment_entity.get("error_description"),
                provider_payment_id=payment_id,
                failure_code=payment_entity.get("error_code"),
            )

    def cancel_booking(self, booking_id: str) -> Booking:
        booking = self.db.query(Booking).filter(
            Booking.booking_id == booking_id
        ).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.status == "CANCELLED":
            raise HTTPException(status_code=400, detail="Booking is already cancelled")

        booking.status = "CANCELLED"
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def cancel_booking_with_refund(self, booking_id: str) -> Booking:
        booking = self.db.query(Booking).filter(
            Booking.booking_id == booking_id
        ).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.status == "CANCELLED":
            raise HTTPException(status_code=400, detail="Booking is already cancelled")

        captured_payment = self.db.query(Payment).filter(
            Payment.booking_id == booking_id,
            Payment.status == "CAPTURED",
        ).first()
        if captured_payment:
            self.refund_payment(captured_payment)

        booking.status = "CANCELLED"
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def refund_booking(self, booking_id: str) -> Booking:
        booking = self.db.query(Booking).filter(
            Booking.booking_id == booking_id
        ).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        captured_payment = self.db.query(Payment).filter(
            Payment.booking_id == booking_id,
            Payment.status == "CAPTURED",
        ).first()
        if not captured_payment:
            raise HTTPException(
                status_code=409,
                detail="No captured payment is available to refund",
            )

        self.refund_payment(captured_payment)
        booking.status = "CANCELLED"
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def refund_payment(self, payment: Payment) -> Payment:
        if payment.status == "REFUNDED":
            return payment
        if payment.status != "CAPTURED" or not payment.provider_payment_id:
            return payment

        refund = self.razorpay.refund_payment(
            payment.provider_payment_id,
            int(payment.amount * 100),
        )
        payment.status = "REFUNDED"
        payment.provider_refund_id = refund.get("id")
        payment.refunded_amount = payment.amount
        payment.refunded_at = datetime.utcnow()
        self.db.commit()
        return payment

    def _mark_failed(
        self,
        payment: Payment,
        failure_message: str | None,
        provider_payment_id: str | None = None,
        failure_code: str | None = None,
    ) -> None:
        payment.status = "FAILED"
        payment.provider_payment_id = provider_payment_id
        payment.failure_code = failure_code
        payment.failure_message = failure_message
        captured_payment = self.db.query(Payment).filter(
            Payment.booking_id == payment.booking_id,
            Payment.status == "CAPTURED",
            Payment.payment_id != payment.payment_id,
        ).first()
        if not captured_payment:
            booking = self.db.query(Booking).filter(
                Booking.booking_id == payment.booking_id
            ).first()
            if booking and booking.status == "CONFIRMED":
                booking.status = "PENDING"
        self.db.commit()

    def _mark_captured(
        self,
        payment: Payment,
        provider_payment_id: str,
        payment_method: str | None = None,
    ) -> None:
        if payment.status == "CAPTURED":
            return
        payment.status = "CAPTURED"
        payment.provider_payment_id = provider_payment_id
        payment.payment_method = payment_method
        payment.paid_at = datetime.utcnow()
        booking = self.db.query(Booking).filter(
            Booking.booking_id == payment.booking_id
        ).first()
        if booking and booking.status not in {"CANCELLED", "COMPLETED"}:
            booking.status = "CONFIRMED"
        self.db.commit()
