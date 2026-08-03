from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from backend.app.domain.auth import AuthenticatedUser, LoginRequest, RegisterRequest, TokenPair

logger = logging.getLogger(__name__)


class AuthProvider(Protocol):
    def authenticate(self, email: str, password: str) -> AuthenticatedUser:
        ...

    def register(self, email: str, password: str, full_name: str | None = None) -> AuthenticatedUser:
        ...

    def refresh_token(self, refresh_token: str) -> TokenPair:
        ...

    def get_user(self, access_token: str) -> AuthenticatedUser:
        ...


class AuthService:
    def __init__(self, provider: AuthProvider) -> None:
        self._provider = provider

    def authenticate(self, request: LoginRequest) -> AuthenticatedUser:
        logger.info("Authenticating user with email=%s", request.email)
        return self._provider.authenticate(request.email, request.password)

    def register(self, request: RegisterRequest) -> AuthenticatedUser:
        logger.info("Registering user with email=%s", request.email)
        return self._provider.register(request.email, request.password, request.full_name)

    def refresh_token(self, refresh_token: str) -> TokenPair:
        logger.info("Refreshing auth token")
        return self._provider.refresh_token(refresh_token)

    def get_user(self, access_token: str) -> AuthenticatedUser:
        logger.info("Resolving authenticated user")
        return self._provider.get_user(access_token)
