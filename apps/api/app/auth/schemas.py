"""Pydantic schemas for authentication (login, registration, tokens)."""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
