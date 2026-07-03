from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.deps import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserProfile
from app.services.auth_service import AuthService

router = APIRouter()
service = AuthService()


@router.post("/register", response_model=UserProfile)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> UserProfile:
    try:
        user = await service.register(db, email=payload.email, password=payload.password, display_name=payload.display_name)
    except ValueError as exc:
        if str(exc) == "email_exists":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from exc
        raise
    return UserProfile.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await service.authenticate(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token, refresh_token = service.create_tokens(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest) -> TokenResponse:
    try:
        access_token, refresh_token = service.refresh_tokens(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout() -> dict[str, str]:
    return {"status": "logged_out"}


@router.get("/me", response_model=UserProfile)
async def me(user=Depends(get_current_user)) -> UserProfile:
    return UserProfile.model_validate(user)
