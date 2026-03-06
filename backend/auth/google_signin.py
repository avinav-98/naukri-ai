from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import sqlite3
from backend.auth.jwt_handler import create_token
from backend.utils.db_migrations import ensure_users_schema

router = APIRouter()

@router.post("/signin-google")
async def google_signin(request: Request):

    data = await request.json()

    email = data.get("email")
    name = data.get("name")

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()
    ensure_users_schema(conn)

    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    if not user:

        cursor.execute("""
            INSERT INTO users (full_name,email,password_hash)
            VALUES (?,?,?)
        """,(name,email,"google"))

        conn.commit()

        cursor.execute("SELECT id FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

    conn.close()

    user_id = user[0]

    token = create_token(user_id)
    response = JSONResponse({"status":"success"})
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False
    )

    return response
