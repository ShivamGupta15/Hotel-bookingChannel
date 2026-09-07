import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [rooms, setRooms] = useState([]);
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [availability, setAvailability] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/rooms/`)
      .then((response) => response.json())
      .then((data) => {
        setRooms(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching rooms:", error);
        setLoading(false);
      });
  }, []);

  async function checkRoomAvailability(roomId) {
    if (!checkIn || !checkOut) {
      alert("Please select check-in and check-out dates");
      return;
    }

    const formatDate = (value) => {
      const [year, month, day] = value.split("-");
      return `${day}-${month}-${year}`;
    };

    const response = await fetch(
      `${API_URL}/api/v1/availability/?room_id=${roomId}&check_in=${formatDate(checkIn)}&check_out=${formatDate(checkOut)}`
    );

    const data = await response.json();

    setAvailability((previous) => ({
      ...previous,
      [roomId]: data.available,
    }));
  }

  if (loading) {
    return <h2>Loading rooms...</h2>;
  }

  return (
    <div className="container">
      <h1>My Hotel</h1>

      <div className="date-selection">
        <div>
          <label>Check-in</label>
          <input
            type="date"
            value={checkIn}
            onChange={(e) => setCheckIn(e.target.value)}
          />
        </div>

        <div>
          <label>Check-out</label>
          <input
            type="date"
            value={checkOut}
            onChange={(e) => setCheckOut(e.target.value)}
          />
        </div>
      </div>

      <h2>Our Rooms</h2>

      <div className="rooms">
        {rooms.map((room) => (
          <div className="room-card" key={room.room_id}>
            <h3>{room.name}</h3>

            <p>{room.description}</p>

            <p>
              <strong>₹{room.price_per_night}</strong> / night
            </p>

            <p>Capacity: {room.capacity} guests</p>

            <button
              onClick={() => checkRoomAvailability(room.room_id)}
            >
              Check Availability
            </button>

            {availability[room.room_id] === true && (
              <p className="available">Available ✓</p>
            )}

            {availability[room.room_id] === false && (
              <p className="unavailable">Not Available ✕</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;