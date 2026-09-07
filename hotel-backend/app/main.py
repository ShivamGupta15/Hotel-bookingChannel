from app.database.base import Base
from app.database.connection import engine
#from app.models.room import Room
from fastapi import FastAPI
#from app.models.booking import Booking
from app.api.routes import bookings,availability
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import rooms, admin


app = FastAPI(
    title="Hotel Booking API",
    description="Backend API for hotel website",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)  # Include the admin router
app.include_router(rooms.router)
app.include_router(bookings.router)
app.include_router(availability.router)  # Include the availability router
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {
        "message": "Hotel API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }