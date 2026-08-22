import pytest


async def test_login_success(client, admin_user):
    resp = await client.post("/api/auth/login", json={"email": "admin@test.local", "password": "TestPass123!"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password_returns_401(client, admin_user):
    resp = await client.post("/api/auth/login", json={"email": "admin@test.local", "password": "wrong"})
    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(client):
    resp = await client.post("/api/auth/login", json={"email": "nobody@test.local", "password": "x"})
    assert resp.status_code == 401


async def test_me_requires_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_me_returns_current_user(client, auth_headers):
    resp = await client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@test.local"


async def test_password_hash_never_returned(client, auth_headers):
    resp = await client.get("/api/auth/me", headers=auth_headers)
    assert "hashed_password" not in resp.json()
    assert "password" not in resp.json()
