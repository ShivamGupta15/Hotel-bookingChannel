from pydantic import BaseModel, ConfigDict, Field
from app.schemas.date import HotelDate


class RoomBase(BaseModel):
    name: str
    description: str | None = None
    price_per_night: int
    capacity: int
    image_url: str | None = None


class RoomCreate(RoomBase):
    pass


class RoomResponse(RoomBase):
    room_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Room Inventory Schemas
# -------------------------

class RoomInventoryCreate(BaseModel):
    room_id: int
    date: HotelDate = Field(
        default_factory=HotelDate.today,
        json_schema_extra={
            "example": HotelDate.today().strftime("%d-%m-%Y")
        }
    )
    available_rooms: int


class RoomInventoryUpdate(BaseModel):
    available_rooms: int = Field(ge=0)


class RoomInventoryResponse(BaseModel):
    inventory_id: int
    room_id: int
    date: HotelDate = Field(..., description="date in dd-mm-yyyy format")
    available_rooms: int

    model_config = ConfigDict(from_attributes=True)