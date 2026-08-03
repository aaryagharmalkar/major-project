from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from backend.app.domain.auth import AuthenticatedUser, TokenPair

logger = logging.getLogger(__name__)


class SupabaseAuthProvider:
    def __init__(self, *, supabase_client: Any | None = None) -> None:
        self._client = supabase_client

    def authenticate(self, email: str, password: str) -> AuthenticatedUser:
        if self._client is None:
            raise RuntimeError("Supabase client is not configured")
        logger.debug("Authenticating with Supabase provider")
        return AuthenticatedUser(
            user_id="supabase-user",
            email=email,
            full_name=email.split("@", 1)[0],
            roles=["investigator"],
            token_pair=TokenPair(access_token="supabase-access", refresh_token="supabase-refresh"),
        )

    def register(self, email: str, password: str, full_name: str | None = None) -> AuthenticatedUser:
        if self._client is None:
            raise RuntimeError("Supabase client is not configured")
        logger.debug("Registering with Supabase provider")
        return AuthenticatedUser(
            user_id="supabase-user",
            email=email,
            full_name=full_name or email.split("@", 1)[0],
            roles=["investigator"],
            token_pair=TokenPair(access_token="supabase-access", refresh_token="supabase-refresh"),
        )

    def refresh_token(self, refresh_token: str) -> TokenPair:
        if self._client is None:
            raise RuntimeError("Supabase client is not configured")
        logger.debug("Refreshing Supabase token")
        return TokenPair(access_token="supabase-access", refresh_token=refresh_token)

    def get_user(self, access_token: str) -> AuthenticatedUser:
        if self._client is None:
            raise RuntimeError("Supabase client is not configured")
        logger.debug("Getting Supabase user")
        return AuthenticatedUser(
            user_id="supabase-user",
            email="supabase@example.com",
            full_name="Supabase User",
            roles=["investigator"],
            token_pair=TokenPair(access_token=access_token, refresh_token="supabase-refresh"),
        )
