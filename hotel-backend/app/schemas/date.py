from datetime import date, datetime
from typing import Annotated

from pydantic import BeforeValidator, PlainSerializer


def parse_hotel_date(value: date | str) -> date:
    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(value, "%d-%m-%Y").date()
    except ValueError as error:
        raise ValueError("Date must be in dd-mm-yyyy format") from error


def format_hotel_date(value: date) -> str:
    return value.strftime("%d-%m-%Y")


HotelDate = Annotated[
    date,
    BeforeValidator(parse_hotel_date),
    PlainSerializer(format_hotel_date, return_type=str),
]