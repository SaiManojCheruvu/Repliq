import pytest


def test_register_success(client, register_payload):
    response = client.post("/auth/register", json=register_payload)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "business_id" in data
    assert data["email"] == register_payload["email"]


def test_register_duplicate_email(client, register_payload):
    client.post("/auth/register", json=register_payload)
    response = client.post("/auth/register", json=register_payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_register_missing_email(client):
    response = client.post("/auth/register", json={
        "password": "test123",
        "business_name": "TestShop"
    })
    assert response.status_code == 422


def test_register_missing_password(client):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "business_name": "TestShop"
    })
    assert response.status_code == 422


def test_register_missing_business_name(client):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "test123"
    })
    assert response.status_code == 422


def test_register_invalid_email(client):
    response = client.post("/auth/register", json={
        "email": "not-an-email",
        "password": "test123",
        "business_name": "TestShop"
    })
    assert response.status_code == 422


def test_login_success(client, register_payload):
    client.post("/auth/register", json=register_payload)
    response = client.post("/auth/login", json={
        "email": register_payload["email"],
        "password": register_payload["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "business_id" in data
    assert data["email"] == register_payload["email"]


def test_login_wrong_password(client, register_payload):
    client.post("/auth/register", json=register_payload)
    response = client.post("/auth/login", json={
        "email": register_payload["email"],
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_user(client):
    response = client.post("/auth/login", json={
        "email": "ghost@example.com",
        "password": "test123"
    })
    assert response.status_code == 401


def test_login_missing_fields(client):
    response = client.post("/auth/login", json={"email": "test@example.com"})
    assert response.status_code == 422


def test_token_is_valid_jwt(client, register_payload):
    from jose import jwt
    import os
    response = client.post("/auth/register", json=register_payload)
    token = response.json()["token"]
    secret = os.getenv("JWT_SECRET", "45640e2dd83973c39e85e19eef8d22394361b25004f33ad45131bd01378f1a66")
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    assert payload["sub"] == register_payload["email"]
    assert "business_id" in payload
    assert "exp" in payload


def test_token_contains_correct_business_id(client, register_payload):
    from jose import jwt
    import os
    response = client.post("/auth/register", json=register_payload)
    data = response.json()
    secret = os.getenv("JWT_SECRET", "45640e2dd83973c39e85e19eef8d22394361b25004f33ad45131bd01378f1a66")
    payload = jwt.decode(data["token"], secret, algorithms=["HS256"])
    assert payload["business_id"] == data["business_id"]