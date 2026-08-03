from __future__ import annotations

from backend.app.application.auth_service import AuthService
from backend.app.domain.auth import AuthenticatedUser, LoginRequest, RegisterRequest, TokenPair


class StubAuthProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def authenticate(self, email: str, password: str) -> AuthenticatedUser:
        self.calls.append(("authenticate", (email, password), {}))
        return AuthenticatedUser(
            user_id="user-1",
            email=email,
            full_name="Test User",
            roles=["investigator"],
            token_pair=TokenPair(access_token="access-token", refresh_token="refresh-token"),
        )

    def register(self, email: str, password: str, full_name: str | None = None) -> AuthenticatedUser:
        self.calls.append(("register", (email, password, full_name), {}))
        return AuthenticatedUser(
            user_id="user-2",
            email=email,
            full_name=full_name or "New User",
            roles=["investigator"],
            token_pair=TokenPair(access_token="access-token", refresh_token="refresh-token"),
        )

    def refresh_token(self, refresh_token: str) -> TokenPair:
        self.calls.append(("refresh_token", (refresh_token,), {}))
        return TokenPair(access_token="new-access", refresh_token=refresh_token)

    def get_user(self, access_token: str) -> AuthenticatedUser:
        self.calls.append(("get_user", (access_token,), {}))
        return AuthenticatedUser(
            user_id="user-1",
            email="test@example.com",
            full_name="Test User",
            roles=["investigator"],
            token_pair=TokenPair(access_token=access_token, refresh_token="refresh-token"),
        )


def test_auth_service_authenticates_users() -> None:
    provider = StubAuthProvider()
    service = AuthService(provider=provider)

    result = service.authenticate(LoginRequest(email="test@example.com", password="secret"))

    assert result.email == "test@example.com"
    assert result.token_pair.access_token == "access-token"
    assert provider.calls[0][0] == "authenticate"


def test_auth_service_registers_users() -> None:
    provider = StubAuthProvider()
    service = AuthService(provider=provider)

    result = service.register(RegisterRequest(email="new@example.com", password="secret", full_name="New User"))

    assert result.email == "new@example.com"
    assert result.full_name == "New User"
    assert provider.calls[0][0] == "register"


def test_auth_service_refreshes_and_reads_user() -> None:
    provider = StubAuthProvider()
    service = AuthService(provider=provider)

    refreshed = service.refresh_token("refresh-token")
    user = service.get_user("access-token")

    assert refreshed.access_token == "new-access"
    assert user.email == "test@example.com"
