from __future__ import annotations

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str
    full_name: str | None = None
    roles: list[str] = Field(default_factory=list)
    token_pair: TokenPair | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None
