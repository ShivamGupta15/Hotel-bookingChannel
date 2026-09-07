# Hotel backend

## Install dependencies

```bash
cd hotel-backend
pip install -r requirements.txt
```

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

Admin sessions expire after 30 minutes.
