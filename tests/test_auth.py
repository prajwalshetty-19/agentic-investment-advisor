"""Tests for registration, authentication, and password security."""

import pytest
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token


def test_password_hashing():
    raw = "MySecurePassword#2026"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("wrongpass", hashed) is False


def test_jwt_token_flow():
    payload = {"sub": "42", "username": "alice"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "42"
    assert decoded["username"] == "alice"


def test_user_registration_success(client):
    res = client.post("/api/auth/register", json={
        "username": "new_trader",
        "email": "trader@example.com",
        "password": "Password123!",
        "risk_tolerance": "BALANCED"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["username"] == "new_trader"


def test_duplicate_registration_rejected(client):
    req_data = {
        "username": "unique_user",
        "email": "unique@example.com",
        "password": "Password123!"
    }
    res1 = client.post("/api/auth/register", json=req_data)
    assert res1.status_code == 201

    # Attempt duplicate username
    res2 = client.post("/api/auth/register", json=req_data)
    assert res2.status_code == 400
    assert "already taken" in res2.json()["detail"]


def test_user_login_flow(client):
    client.post("/api/auth/register", json={
        "username": "login_user",
        "email": "login@example.com",
        "password": "SecurePassword1!"
    })

    # Valid login
    login_res = client.post("/api/auth/login", json={
        "username_or_email": "login_user",
        "password": "SecurePassword1!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data

    # Invalid login
    bad_res = client.post("/api/auth/login", json={
        "username_or_email": "login_user",
        "password": "WrongPassword!"
    })
    assert bad_res.status_code == 401
