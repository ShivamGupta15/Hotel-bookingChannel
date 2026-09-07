# Hotel backend

## Install dependencies

```bash
cd hotel-backend
pip install -r requirements.txt
```
## Run mysql server
Create mysql server and copy its address to .env as shown .env.example
run command
'''CREATE DATABASE hotel_db;'''
'''USE hotel_db;'''

## Admin session

Create a local environment file from the template:

```bash
cd hotel-backend
cp .env.example .env
```

Generate a new cryptographically secure JWT signing key:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Copy the generated value into `.env` as `JWT_SECRET_KEY`:

```dotenv
JWT_SECRET_KEY="paste-the-generated-value-here"
```

Keep this key private. Changing it invalidates all existing admin tokens. The `.env` file is ignored by Git.

Configure these environment variables in `.env` before starting the API:

- `JWT_SECRET_KEY`: a long, random signing secret.
- `ADMIN_USERNAME`: the admin login name.
- `ADMIN_PASSWORD_HASH`: a scrypt hash for the admin password.

You can verify that the key is set without printing it:

```bash
python -c 'from dotenv import dotenv_values; assert dotenv_values(".env").get("JWT_SECRET_KEY"); print("JWT_SECRET_KEY is configured")'
```

Generate a password hash with:

```bash
python -c 'from app.security import hash_password; print(hash_password(input("Password: ")))'
```

Start the API from the `hotel-backend` directory:

```bash
uvicorn app.main:app --reload
```


Log in with `POST /admin/login`:

```json
{"username":"admin","password":"your-password"}
```

Send the returned token when updating inventory:

```text
Authorization: Bearer <access_token>
```

Admin sessions expire after 60 minutes.

## Razorpay payments

Configure these environment variables before starting the API:

```dotenv
RAZORPAY_KEY_ID="your-key-id"
RAZORPAY_KEY_SECRET="your-key-secret"
RAZORPAY_WEBHOOK_SECRET="your-webhook-secret"
```

`API_KEY` and `SECRET_KEY` are also accepted as backwards-compatible names for
the Razorpay key ID and key secret. Configure `RAZORPAY_WEBHOOK_SECRET` for
webhook verification.

Payment endpoints:

- `POST /api/v1/payments/orders` creates one Razorpay order and local payment attempt.
- `POST /api/v1/payments/verify` verifies the checkout signature and confirms the booking.
- `POST /api/v1/payments/webhook` verifies Razorpay webhook signatures and processes payment events.
- `PUT /api/v1/bookings/{booking_id}/cancel` lets a customer cancel and refunds its captured payment.
- `PUT /admin/bookings/{booking_id}/cancel` lets an authenticated admin cancel without refunding.
- `PUT /admin/bookings/{booking_id}/refund` issues a full refund and cancels the booking.

Install dependencies with `pip install -r requirements.txt`.



# Run uvicorn
''' uvicorn app.main:app --reload '''
run it from /home-backend/ directory



# Swagger UI for endpoints
to access swagger UI go to your server address followed by /docs
example: 
 localhost:8000/docs
