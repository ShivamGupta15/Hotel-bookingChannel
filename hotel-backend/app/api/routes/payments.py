import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.integrations.razorpay_client import RazorpayClient
from app.schemas.payment import (
    PaymentOrderCreate,
    PaymentOrderResponse,
    PaymentResponse,
    PaymentVerifyRequest,
)
from app.services.payment_service import PaymentService


router = APIRouter(
    prefix="/api/v1/payments",
    tags=["Payments"],
)


@router.post("/orders", response_model=PaymentOrderResponse)
def create_payment_order(
    request: PaymentOrderCreate,
    db: Session = Depends(get_db),
):
    payment = PaymentService(db).create_order(request)
    return PaymentOrderResponse(
        payment_id=payment.payment_id,
        booking_id=payment.booking_id,
        provider=payment.provider,
        provider_order_id=payment.provider_order_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        razorpay_key_id=RazorpayClient().key_id,
    )


@router.post("/verify", response_model=PaymentResponse)
def verify_payment(
    request: PaymentVerifyRequest,
    db: Session = Depends(get_db),
):
    return PaymentService(db).verify_payment(request)


@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(...),
    db: Session = Depends(get_db),
):
    body = await request.body()
    try:
        client = RazorpayClient()
        client.verify_webhook_signature(body.decode("utf-8"), x_razorpay_signature)
        event = json.loads(body)
    except (ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from error
    except Exception as error:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from error

    PaymentService(db, client).process_webhook(event)
    return None
