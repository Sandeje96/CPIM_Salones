import os
import secrets
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

password_hash = PasswordHash((Argon2Hasher(),))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def init_session(request: Request, user_id: int, rol: str):
    request.session.clear()
    request.session["user_id"] = user_id
    request.session["rol"] = rol
    request.session["csrf_token"] = secrets.token_urlsafe(32)

def require_login(request: Request):
    if "user_id" not in request.session:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND, 
            headers={"Location": "/admin/login"}
        )
    return request.session["user_id"]

def require_role(request: Request, rol: str):
    user_id = require_login(request)
    if request.session.get("rol") != rol:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
    return user_id

def require_any_role(request: Request, roles: list):
    user_id = require_login(request)
    if request.session.get("rol") not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
    return user_id

async def verify_csrf(request: Request):
    """
    Verifica que el CSRF token del formulario o header coincida con el de la sesión.
    Se requiere para todos los POST/PUT/DELETE del admin.
    """
    if request.method not in ["POST", "PUT", "DELETE"]:
        return
    
    session_token = request.session.get("csrf_token")
    if not session_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing in session")

    # Intentar obtener del form
    form = await request.form()
    request_token = form.get("csrf_token")
    
    # Si no, buscar en header (HTMX por ejemplo)
    if not request_token:
        request_token = request.headers.get("X-CSRF-Token")

    if not request_token or not secrets.compare_digest(session_token, request_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token mismatch")
