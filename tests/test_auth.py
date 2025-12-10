from fastapi.testclient import TestClient


def test_register_new_user(client: TestClient) -> None:
    payload = {
        "email": "user1@example.com",
        "username": "user1",
        "password": "password123",
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201, resp.text

    data = resp.json()
    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert "id" in data
    assert "created_at" in data


def test_register_duplicate_user(client: TestClient) -> None:
    payload = {
        "email": "user2@example.com",
        "username": "user2",
        "password": "password123",
    }
    r1 = client.post("/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 400
    body = r2.json()
    assert "error" in body
    assert body["error"]["code"] == "user_exists"


def test_login_with_email_and_username(client: TestClient) -> None:
    payload = {
        "email": "user3@example.com",
        "username": "user3",
        "password": "password123",
    }
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201

    r_email = client.post(
        "/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r_email.status_code == 200, r_email.text
    token_email = r_email.json()
    assert "access_token" in token_email

    r_username = client.post(
        "/auth/login",
        data={
            "username": payload["username"],
            "password": payload["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r_username.status_code == 200, r_username.text
    token_username = r_username.json()
    assert "access_token" in token_username


def test_login_invalid_credentials(client: TestClient) -> None:
    r = client.post(
        "/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "wrong",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "invalid_credentials"
