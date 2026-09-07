from pydantic import BaseModel, Field

from app.schemas.date import HotelDate


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class BulkInventoryUpdateRequest(BaseModel):
    room_id: int
    dates: list[HotelDate] = Field(
        min_length=1,
        description="Inventory dates in dd-mm-yyyy format",
        json_schema_extra={"example": ["07-09-2026", "10-09-2026"]},
    )
    available_rooms: int = Field(ge=0)


class BulkInventoryUpdateResponse(BaseModel):
    room_id: int
    dates: list[HotelDate] = Field(
        ..., description="Inventory dates in dd-mm-yyyy format"
    )
    available_rooms: int
    created_count: int
    updated_count: int