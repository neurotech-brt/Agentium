"""
Authentication API for frontend.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.core.auth import create_access_token, verify_token
from backend.models.entities.audit import AuditLog, AuditLevel, AuditCategory

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# Sovereign credentials (in production: database with hashed passwords)
SOVEREIGN_CREDENTIALS = {
    "admin": "admin"  # Change in production!
}

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Authenticate user and return JWT token."""
    
    # Verify credentials
    if credentials.username not in SOVEREIGN_CREDENTIALS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if SOVEREIGN_CREDENTIALS[credentials.username] != credentials.password:
        # Log failed attempt
        AuditLog.log(
            level=AuditLevel.WARNING,
            category=AuditCategory.AUTHENTICATION,
            actor_type="user",
            actor_id=credentials.username,
            action="login_failed",
            description="Failed login attempt",
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create token
    token_data = {
        "sub": credentials.username,
        "role": "sovereign",
        "iat": datetime.utcnow()
    }
    access_token = create_access_token(token_data)
    
    # Log success
    AuditLog.log(
        level=AuditLevel.INFO,
        category=AuditCategory.AUTHENTICATION,
        actor_type="user",
        actor_id=credentials.username,
        action="login_success",
        description="User logged in successfully"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": credentials.username,
            "role": "sovereign"
        }
    }

@router.post("/verify")
async def verify_token_endpoint(token: str):
    """Verify if token is valid."""
    payload = verify_token(token)
    if payload:
        return {"valid": True, "user": payload}
    return {"valid": False}


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user)
):
    """Change sovereign password."""
    # Verify old password matches
    if SOVEREIGN_CREDENTIALS.get(current_user["sub"]) != old_password:
        raise HTTPException(status_code=400, detail="Old password incorrect")
    
    # Update password
    SOVEREIGN_CREDENTIALS[current_user["sub"]] = new_password
    
    AuditLog.log(
        level=AuditLevel.INFO,
        category=AuditCategory.AUTHENTICATION,
        actor_type="user",
        actor_id=current_user["sub"],
        action="password_changed",
        description="Password changed successfully"
    )
    
    return {"status": "success"}