from __future__ import annotations

from backend.app.domain.auth import LoginRequest, RegisterRequest, TokenPair


def test_login_request_validation() -> None:
    request = LoginRequest(email="user@example.com", password="secret")
    assert request.email == "user@example.com"


def test_register_request_validation() -> None:
    request = RegisterRequest(email="user@example.com", password="secret", full_name="User")
    assert request.full_name == "User"


def test_token_pair_model() -> None:
    token_pair = TokenPair(access_token="a", refresh_token="b")
    assert token_pair.access_token == "a"
