import os
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="pkg_resources is deprecated as an API.*",
        category=UserWarning,
    )
    import razorpay


class RazorpayClient:
    def __init__(self) -> None:
        key_id = os.getenv("RAZORPAY_KEY_ID") or os.getenv("API_KEY")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET") or os.getenv("SECRET_KEY")
        if not key_id or not key_secret:
            raise RuntimeError(
                "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be configured"
            )

        self.key_id = key_id
        self.client = razorpay.Client(auth=(key_id, key_secret))

    def create_order(self, amount: int, currency: str, receipt: str) -> dict:
        return self.client.order.create({
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "payment_capture": 1,
        })

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> None:
        self.client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })

    def verify_webhook_signature(self, body: str, signature: str) -> None:
        webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        if not webhook_secret:
            raise RuntimeError("RAZORPAY_WEBHOOK_SECRET must be configured")
        self.client.utility.verify_webhook_signature(
            body,
            signature,
            webhook_secret,
        )

    def fetch_payment(self, payment_id: str) -> dict:
        return self.client.payment.fetch(payment_id)

    def refund_payment(self, payment_id: str, amount_paise: int) -> dict:
        return self.client.payment.refund(payment_id, {
            "amount": amount_paise,
        })
