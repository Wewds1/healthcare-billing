# This is for Role based access control (RBAC) implementation
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials 
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.core.dependencies import get_db
from app.crud import user as user_crud


security = HTTPBearer()

# extract and validate jwt and return user info
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials 
    payload = decode_access_token(token)

    # check if token is valid
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    username = payload.get("sub")

    # check if user exists
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    user = user_crud.get_user_by_username(db, username=username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def require_role(required_role: list):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Allowed Roles: {required_role}",
            )
        return current_user
    return role_checker


require_admin = require_role(["admin"])
require_user = require_role(["admin", "user"])