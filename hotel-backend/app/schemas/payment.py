from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentOrderCreate(BaseModel):
    booking_id: str
    amount_paise: int = Field(gt=0, description="Amount in the smallest currency unit")
    currency: str = Field(default="INR", min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=8, max_length=255)


class PaymentOrderResponse(BaseModel):
    payment_id: int
    booking_id: str
    provider: str
    provider_order_id: str
    amount: Decimal
    currency: str
    status: str
    razorpay_key_id: str

    model_config = ConfigDict(from_attributes=True)


class PaymentVerifyRequest(BaseModel):
    payment_id: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    payment_id: int
    booking_id: str
    provider: str
    provider_order_id: str | None
    provider_payment_id: str | None
    provider_signature: str | None
    provider_refund_id: str | None
    amount: Decimal
    currency: str
    status: str
    failure_code: str | None
    failure_message: str | None
    refunded_amount: Decimal

    model_config = ConfigDict(from_attributes=True)
