import { useEffect, useRef, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [rooms, setRooms] = useState([]);
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [availability, setAvailability] = useState({});
  const [bookingRoomId, setBookingRoomId] = useState(null);
  const [bookingGuestName, setBookingGuestName] = useState("");
  const [bookingEmail, setBookingEmail] = useState("");
  const [bookingPhone, setBookingPhone] = useState("");
  const [bookingGuests, setBookingGuests] = useState("1");
  const [bookingCoupon, setBookingCoupon] = useState("");
  const [bookingMessage, setBookingMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [adminMode, setAdminMode] = useState(false);
  const [adminSection, setAdminSection] = useState("inventory");
  const [adminBookings, setAdminBookings] = useState([]);
  const [adminBookingsMessage, setAdminBookingsMessage] = useState("");
  const [adminCoupons, setAdminCoupons] = useState([]);
  const [couponForm, setCouponForm] = useState({
    code: "",
    discount_type: "PERCENTAGE",
    discount_value: "",
    max_discount: "",
    valid_from: "",
    valid_until: "",
    usage_limit: "",
  });
  const [adminToken, setAdminToken] = useState(
    () => localStorage.getItem("hotel_admin_token") || ""
  );
  const [adminUsername, setAdminUsername] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [inventoryRoomId, setInventoryRoomId] = useState("");
  const [inventoryDates, setInventoryDates] = useState([]);
  const [inventoryCount, setInventoryCount] = useState("");
  const [inventoryMessage, setInventoryMessage] = useState("");
  const [inventoryStartDate, setInventoryStartDate] = useState("");
  const [inventoryEndDate, setInventoryEndDate] = useState("");
  const [calendarMonth, setCalendarMonth] = useState(() => new Date());
  const draggingCalendar = useRef(false);
  const calendarAnchor = useRef("");

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

  const dateKey = (value) => {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, "0");
    const day = String(value.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const dateFromKey = (value) => {
    const [year, month, day] = value.split("-").map(Number);
    return new Date(year, month - 1, day);
  };

  const datesBetween = (firstDate, secondDate) => {
    const first = dateFromKey(firstDate);
    const second = dateFromKey(secondDate);
    const start = first <= second ? first : second;
    const end = first <= second ? second : first;
    const dates = [];
    const current = new Date(start);

    while (current <= end) {
      dates.push(dateKey(current));
      current.setDate(current.getDate() + 1);
    }
    return dates;
  };

  function getCalendarDays() {
    const firstOfMonth = new Date(
      calendarMonth.getFullYear(),
      calendarMonth.getMonth(),
      1,
    );
    const firstVisibleDay = new Date(firstOfMonth);
    firstVisibleDay.setDate(firstOfMonth.getDate() - firstOfMonth.getDay());

    return Array.from({ length: 42 }, (_, index) => {
      const day = new Date(firstVisibleDay);
      day.setDate(firstVisibleDay.getDate() + index);
      return day;
    });
  }

  function selectCalendarRange(date) {
    const selectedDate = dateKey(date);
    const anchor = calendarAnchor.current || selectedDate;
    const startDate = anchor <= selectedDate ? anchor : selectedDate;
    const endDate = anchor <= selectedDate ? selectedDate : anchor;
    setInventoryStartDate(startDate);
    setInventoryEndDate(endDate);
    setInventoryDates(datesBetween(startDate, endDate));
  }

  function calendarDateFromEvent(event) {
    const dayButton = document
      .elementFromPoint(event.clientX, event.clientY)
      ?.closest("[data-calendar-date]");
    return dayButton ? dateFromKey(dayButton.dataset.calendarDate) : null;
  }

  function startCalendarDrag(event) {
    const day = calendarDateFromEvent(event);
    if (!day) return;
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    draggingCalendar.current = true;
    calendarAnchor.current = dateKey(day);
    selectCalendarRange(day);
  }

  function moveCalendarDrag(event) {
    if (!draggingCalendar.current) return;
    const day = calendarDateFromEvent(event);
    if (day) selectCalendarRange(day);
  }

  function finishCalendarDrag(event) {
    draggingCalendar.current = false;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  function moveCalendarMonth(amount) {
    setCalendarMonth((month) => new Date(
      month.getFullYear(),
      month.getMonth() + amount,
      1,
    ));
  }

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

  async function submitBooking(event) {
    event.preventDefault();
    if (!checkIn || !checkOut || bookingRoomId === null) {
      setBookingMessage("Select check-in and check-out dates first.");
      return;
    }

    const formatDate = (value) => {
      const [year, month, day] = value.split("-");
      return `${day}-${month}-${year}`;
    };

    setBookingMessage("Creating booking...");
    try {
      const response = await fetch(`${API_URL}/api/v1/bookings/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          room_id: bookingRoomId,
          guest_name: bookingGuestName,
          email: bookingEmail,
          phone: bookingPhone,
          check_in: formatDate(checkIn),
          check_out: formatDate(checkOut),
          guests: Number(bookingGuests),
          coupon_code: bookingCoupon.trim() || null,
        }),
      });
      const booking = await response.json();
      if (!response.ok) {
        setBookingMessage(booking.detail || `Booking failed (${response.status}).`);
        return;
      }

      const amountPaise = Math.round(Number(booking.total_amount) * 100);
      const orderResponse = await fetch(`${API_URL}/api/v1/payments/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          booking_id: booking.booking_id,
          amount_paise: amountPaise,
          currency: "INR",
          idempotency_key: `${booking.booking_id}-${Date.now()}`,
        }),
      });
      const order = await orderResponse.json();
      if (!orderResponse.ok) {
        setBookingMessage(order.detail || "Could not create payment order.");
        return;
      }

      if (!window.Razorpay) {
        setBookingMessage("Razorpay Checkout could not be loaded.");
        return;
      }

      const razorpay = new window.Razorpay({
        key: order.razorpay_key_id,
        amount: amountPaise,
        currency: order.currency,
        name: "My Hotel",
        description: `Booking ${booking.booking_id}`,
        order_id: order.provider_order_id,
        prefill: {
          name: bookingGuestName,
          email: bookingEmail,
          contact: bookingPhone,
        },
        handler: async (checkoutResponse) => {
          setBookingMessage("Verifying payment...");
          const verifyResponse = await fetch(`${API_URL}/api/v1/payments/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              payment_id: order.payment_id,
              razorpay_order_id: checkoutResponse.razorpay_order_id,
              razorpay_payment_id: checkoutResponse.razorpay_payment_id,
              razorpay_signature: checkoutResponse.razorpay_signature,
            }),
          });
          const verification = await verifyResponse.json();
          setBookingMessage(verifyResponse.ok
            ? `Payment successful. Booking ${booking.booking_id} is confirmed.`
            : verification.detail || "Payment verification failed.");
        },
        modal: {
          ondismiss: () => setBookingMessage("Payment was cancelled.")
        },
      });

      razorpay.open();
    } catch (error) {
      console.error("Booking failed:", error);
      setBookingMessage("Could not reach the booking service.");
    }
  }

  async function loginAdmin(event) {
    event.preventDefault();
    const response = await fetch(`${API_URL}/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: adminUsername, password: adminPassword }),
    });
    if (!response.ok) {
      setInventoryMessage("Admin login failed.");
      return;
    }
    const data = await response.json();
    localStorage.setItem("hotel_admin_token", data.access_token);
    setAdminToken(data.access_token);
    setAdminPassword("");
    setInventoryMessage("");
  }

  async function loadAdminBookings() {
    setAdminBookingsMessage("Loading bookings...");
    try {
      const response = await fetch(`${API_URL}/admin/bookings`, {
        headers: { Authorization: `Bearer ${adminToken}` },
      });
      const data = await response.json();
      if (response.status === 401) {
        localStorage.removeItem("hotel_admin_token");
        setAdminToken("");
        setAdminBookingsMessage("Your admin session expired. Please sign in again.");
        return;
      }
      if (!response.ok) {
        setAdminBookingsMessage(data.detail || "Could not load bookings.");
        return;
      }
      setAdminBookings(data);
      setAdminBookingsMessage("");
    } catch (error) {
      console.error("Admin booking list failed:", error);
      setAdminBookingsMessage("Could not reach the backend.");
    }
  }

  async function runAdminBookingAction(bookingId, action) {
    const confirmationMessage = {
      confirm: `Confirm booking ${bookingId}? This will mark the booking as CONFIRMED.`,
      cancel: `Cancel booking ${bookingId}? This changes only the booking status. No refund will be issued.`,
      refund: `Refund booking ${bookingId}? This will issue a full Razorpay refund and cancel the booking. This action cannot be undone.`,
    }[action];
    if (!window.confirm(confirmationMessage)) return;
    setAdminBookingsMessage(`${action}ing booking...`);
    try {
      const response = await fetch(`${API_URL}/admin/bookings/${bookingId}/${action}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${adminToken}` },
      });
      const data = await response.json();
      if (!response.ok) {
        setAdminBookingsMessage(data.detail || `${action} failed.`);
        return;
      }
      await loadAdminBookings();
    } catch (error) {
      console.error(`Admin ${action} failed:`, error);
      setAdminBookingsMessage(`Could not ${action} booking.`);
    }
  }

  async function loadAdminCoupons() {
    const response = await fetch(`${API_URL}/admin/coupons`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    if (response.ok) setAdminCoupons(await response.json());
  }

  async function createAdminCoupon(event) {
    event.preventDefault();
    setAdminBookingsMessage("Creating coupon...");
    const payload = {
      ...couponForm,
      discount_value: Number(couponForm.discount_value),
      max_discount: couponForm.max_discount ? Number(couponForm.max_discount) : null,
      usage_limit: couponForm.usage_limit ? Number(couponForm.usage_limit) : null,
      valid_from: couponForm.valid_from || null,
      valid_until: couponForm.valid_until || null,
    };
    const response = await fetch(`${API_URL}/admin/coupons`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${adminToken}`,
      },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      setAdminBookingsMessage(data.detail || "Could not create coupon.");
      return;
    }
    setCouponForm({ code: "", discount_type: "PERCENTAGE", discount_value: "", max_discount: "", valid_from: "", valid_until: "", usage_limit: "" });
    setAdminBookingsMessage(`Coupon ${data.code} created.`);
    loadAdminCoupons();
  }

  function displayInventoryDate(value) {
    const [year, month, day] = value.split("-");
    return `${day}-${month}-${year}`;
  }

  async function submitBulkInventory(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const roomId = form.elements.roomId.value;
    const startDate = form.elements.startDate.value;
    const endDate = form.elements.endDate.value;
    const availableRooms = form.elements.availableRooms.value;
    const selectedDates = startDate && endDate
      ? datesBetween(startDate, endDate)
      : [];

    if (!roomId) {
      setInventoryMessage("Select a room before updating inventory.");
      return;
    }
    if (!startDate) {
      setInventoryMessage("Select a start date before updating inventory.");
      return;
    }
    if (!endDate) {
      setInventoryMessage("Select an end date before updating inventory.");
      return;
    }
    if (endDate < startDate) {
      setInventoryMessage("End date must be on or after the start date.");
      return;
    }
    if (availableRooms === "") {
      setInventoryMessage("Enter the available room count before updating inventory.");
      return;
    }
    if (!selectedDates.length) {
      setInventoryMessage("The selected date range does not contain any dates.");
      return;
    }

    const formatDate = (value) => {
      const [year, month, day] = value.split("-");
      return `${day}-${month}-${year}`;
    };
    setInventoryMessage("Updating inventory...");
    try {
      const response = await fetch(`${API_URL}/admin/inventory/bulk`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${adminToken}`,
        },
        body: JSON.stringify({
          room_id: Number(roomId),
          dates: selectedDates.map(formatDate),
          available_rooms: Number(availableRooms),
        }),
      });
      const data = await response.json();
      if (response.status === 401) {
        localStorage.removeItem("hotel_admin_token");
        setAdminToken("");
        setInventoryMessage("Your admin session expired. Please sign in again.");
        return;
      }
      setInventoryMessage(response.ok
        ? `Updated ${data.created_count + data.updated_count} inventory entries.`
        : data.detail || `Inventory update failed (${response.status}).`);
    } catch (error) {
      console.error("Bulk inventory update failed:", error);
      setInventoryMessage("Could not reach the backend. Confirm Uvicorn is running on 127.0.0.1:8000.");
    }
  }

  if (loading) {
    return <h2>Loading rooms...</h2>;
  }

  return (
    <div className="container">
      <h1>My Hotel</h1>
      <button className="admin-toggle" onClick={() => setAdminMode((mode) => !mode)}>
        {adminMode ? "Guest view" : "Manage inventory"}
      </button>

      {adminMode && (
        <section className="inventory-panel">
          {!adminToken ? (
            <form className="inventory-login" onSubmit={loginAdmin}>
              <label>Username<input value={adminUsername} onChange={(event) => setAdminUsername(event.target.value)} required /></label>
              <label>Password<input type="password" value={adminPassword} onChange={(event) => setAdminPassword(event.target.value)} required /></label>
              <button type="submit">Sign in</button>
            </form>
          ) : (
            <>
              <div className="admin-section-tabs">
                <button type="button" className={adminSection === "inventory" ? "active" : ""} onClick={() => setAdminSection("inventory")}>Inventory</button>
                <button type="button" className={adminSection === "bookings" ? "active" : ""} onClick={() => { setAdminSection("bookings"); loadAdminBookings(); }}>Bookings</button>
                <button type="button" className={adminSection === "coupons" ? "active" : ""} onClick={() => { setAdminSection("coupons"); loadAdminCoupons(); }}>Coupons</button>
              </div>
              {adminSection === "inventory" && <>
              <h2>Bulk inventory update</h2>
              <p className="calendar-instructions">Choose a start date and an end date to update every date in between.</p>
              <form className="inventory-form" onSubmit={submitBulkInventory}>
              <label>Room<select name="roomId" value={inventoryRoomId} onChange={(event) => setInventoryRoomId(event.target.value)} required>
                <option value="">Select a room</option>
                {rooms.map((room) => <option key={room.room_id} value={room.room_id}>{room.name} (ID {room.room_id})</option>)}
              </select></label>
              <input name="startDate" type="hidden" value={inventoryStartDate} readOnly />
              <input name="endDate" type="hidden" value={inventoryEndDate} readOnly />
              <div className="calendar-picker">
                <div className="calendar-header">
                  <button type="button" onClick={() => moveCalendarMonth(-1)} aria-label="Previous month">&lt;</button>
                  <strong>{calendarMonth.toLocaleDateString("en-US", { month: "long", year: "numeric" })}</strong>
                  <button type="button" onClick={() => moveCalendarMonth(1)} aria-label="Next month">&gt;</button>
                </div>
                <div className="calendar-weekdays">
                  {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => <span key={day}>{day}</span>)}
                </div>
                <div
                  className="calendar-grid"
                  onPointerDown={startCalendarDrag}
                  onPointerMove={moveCalendarDrag}
                  onPointerUp={finishCalendarDrag}
                  onPointerCancel={finishCalendarDrag}
                >
                  {getCalendarDays().map((date) => {
                    const key = dateKey(date);
                    const inMonth = date.getMonth() === calendarMonth.getMonth();
                    const selected = inventoryDates.includes(key);
                    return (
                      <button
                        type="button"
                        key={key}
                        data-calendar-date={key}
                        className={`${inMonth ? "" : "outside-month"} ${selected ? "selected-day" : ""}`}
                      >
                        {date.getDate()}
                      </button>
                    );
                  })}
                </div>
                <p className="calendar-selection">
                  {inventoryStartDate && inventoryEndDate
                    ? `${displayInventoryDate(inventoryStartDate)} - ${displayInventoryDate(inventoryEndDate)}`
                    : "Drag from a start date to an end date"}
                </p>
              </div>
              <div className="selected-dates">
                {inventoryDates.map((date) => <button type="button" key={date} onClick={() => setInventoryDates((dates) => dates.filter((item) => item !== date))}>{displayInventoryDate(date)} ×</button>)}
              </div>
              <label>Available rooms<input name="availableRooms" type="number" min="0" value={inventoryCount} onChange={(event) => setInventoryCount(event.target.value)} required /></label>
              <button type="submit">Update inventory</button>
              </form>
              </>}
              {adminSection === "bookings" && <section className="booking-admin-section">
                <div className="booking-admin-header"><h2>Bookings</h2><button type="button" onClick={loadAdminBookings}>Refresh</button></div>
                {adminBookingsMessage && <p className="inventory-message">{adminBookingsMessage}</p>}
                <div className="booking-table-wrapper"><table className="booking-table"><thead><tr><th>Booking</th><th>Guest</th><th>Contact</th><th>Dates</th><th>Payment</th><th>Razorpay IDs</th><th>Signature</th><th>Actions</th></tr></thead><tbody>
                  {adminBookings.map((booking) => <tr key={booking.booking_id}>
                    <td><strong>{booking.booking_id}</strong><br />Status: {booking.booking_status}<br /><span className="admin-activity">{booking.admin_activity || "No activity recorded"}</span></td>
                    <td>{booking.guest_name}</td>
                    <td>{booking.phone}<br />{booking.email}</td>
                    <td>{booking.check_in}<br />{booking.check_out}</td>
                    <td>{booking.payment_status || "No payment"}<br />Amount: {booking.payment_amount ? `₹${booking.payment_amount}` : "-"}<br />Refunded: ₹{booking.refunded_amount}<br />Coupon: {booking.coupon_code || "-"}<br />Discount: ₹{booking.discount_amount || "0.00"}</td>
                    <td className="monospace">Order: {booking.razorpay_order_id || "-"}<br />Payment: {booking.razorpay_payment_id || "-"}</td>
                    <td className="signature-cell">{booking.razorpay_signature || "-"}</td>
                    <td className="booking-actions"><button type="button" disabled={booking.booking_status === "CANCELLED"} onClick={() => runAdminBookingAction(booking.booking_id, "confirm")}>Confirm</button><button type="button" disabled={booking.booking_status === "CANCELLED"} onClick={() => runAdminBookingAction(booking.booking_id, "cancel")}>Cancel</button><button type="button" disabled={booking.payment_status !== "CAPTURED"} onClick={() => runAdminBookingAction(booking.booking_id, "refund")}>Refund</button></td>
                  </tr>)}
                </tbody></table></div>
              </section>}
              {adminSection === "coupons" && <section className="booking-admin-section">
                <h2>Coupons</h2>
                <form className="coupon-form" onSubmit={createAdminCoupon}>
                  <label>Code<input value={couponForm.code} onChange={(event) => setCouponForm({ ...couponForm, code: event.target.value.toUpperCase() })} required /></label>
                  <label>Type<select value={couponForm.discount_type} onChange={(event) => setCouponForm({ ...couponForm, discount_type: event.target.value })}><option value="PERCENTAGE">Percentage</option><option value="FIXED">Fixed amount</option></select></label>
                  <label>Discount<input type="number" min="0.01" step="0.01" value={couponForm.discount_value} onChange={(event) => setCouponForm({ ...couponForm, discount_value: event.target.value })} required /></label>
                  <label>Max discount<input type="number" min="0.01" step="0.01" value={couponForm.max_discount} onChange={(event) => setCouponForm({ ...couponForm, max_discount: event.target.value })} /></label>
                  <label>Valid from<input type="date" value={couponForm.valid_from} onChange={(event) => setCouponForm({ ...couponForm, valid_from: event.target.value })} /></label>
                  <label>Valid until<input type="date" value={couponForm.valid_until} onChange={(event) => setCouponForm({ ...couponForm, valid_until: event.target.value })} /></label>
                  <label>Usage limit<input type="number" min="1" value={couponForm.usage_limit} onChange={(event) => setCouponForm({ ...couponForm, usage_limit: event.target.value })} /></label>
                  <button type="submit">Create coupon</button>
                </form>
                {adminBookingsMessage && <p className="inventory-message">{adminBookingsMessage}</p>}
                <div className="coupon-list">{adminCoupons.map((coupon) => <div className="coupon-row" key={coupon.coupon_id}><strong>{coupon.code}</strong><span>{coupon.discount_type === "PERCENTAGE" ? `${coupon.discount_value}%` : `₹${coupon.discount_value}`}</span><span>Used {coupon.used_count}{coupon.usage_limit ? ` / ${coupon.usage_limit}` : ""}</span><span>{coupon.is_active ? "Active" : "Inactive"}</span></div>)}</div>
              </section>}
            </>
          )}
          {inventoryMessage && <p className="inventory-message">{inventoryMessage}</p>}
        </section>
      )}

      {!adminMode && <div className="date-selection">
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
      </div>}

      {!adminMode && <h2>Our Rooms</h2>}

      {!adminMode && <div className="rooms">
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
              <button
                className="book-button"
                onClick={() => {
                  setBookingRoomId(room.room_id);
                  setBookingMessage("");
                }}
              >
                Book this room
              </button>
            )}

            {availability[room.room_id] === true && (
              <p className="available">Available ✓</p>
            )}

            {availability[room.room_id] === false && (
              <p className="unavailable">Not Available ✕</p>
            )}

            {bookingRoomId === room.room_id && (
              <form className="booking-form" onSubmit={submitBooking}>
                <label>Name<input value={bookingGuestName} onChange={(event) => setBookingGuestName(event.target.value)} required /></label>
                <label>Email<input type="email" value={bookingEmail} onChange={(event) => setBookingEmail(event.target.value)} required /></label>
                <label>Phone<input type="tel" minLength="10" maxLength="15" value={bookingPhone} onChange={(event) => setBookingPhone(event.target.value)} required /></label>
                <label>Guests<input type="number" min="1" value={bookingGuests} onChange={(event) => setBookingGuests(event.target.value)} required /></label>
                <label>Coupon code<input value={bookingCoupon} onChange={(event) => setBookingCoupon(event.target.value)} placeholder="Optional" /></label>
                <button type="submit">Confirm booking</button>
                <button type="button" className="cancel-button" onClick={() => setBookingRoomId(null)}>Cancel</button>
                {bookingMessage && <p className="booking-message">{bookingMessage}</p>}
              </form>
            )}
          </div>
        ))}
      </div>}
    </div>
  );
}

export default App;