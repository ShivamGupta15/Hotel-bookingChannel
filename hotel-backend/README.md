# Hotel backend

## Admin session

Configure these environment variables before starting the API:

- `JWT_SECRET_KEY`: a long, random signing secret.
- `ADMIN_USERNAME`: the admin login name.
- `ADMIN_PASSWORD_HASH`: a scrypt hash for the admin password.

Generate a password hash with:

```bash
python -c 'from app.security import hash_password; print(hash_password(input("Password: ")))' 
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