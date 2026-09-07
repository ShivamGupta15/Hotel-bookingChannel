from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CouponCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    discount_type: str = Field(pattern="^(PERCENTAGE|FIXED)$")
    discount_value: Decimal = Field(gt=0)
    max_discount: Decimal | None = Field(default=None, gt=0)
    valid_from: date | None = None
    valid_until: date | None = None
    usage_limit: int | None = Field(default=None, gt=0)


class CouponResponse(CouponCreate):
    coupon_id: int
    used_count: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
