from decimal import Decimal

from fastapi.testclient import TestClient


def register_and_login(client: TestClient, idx: int = 1) -> dict:
    """
    Вспомогательная функция:
    регистрирует пользователя user{idx} и возвращает заголовок Authorization.
    """
    email = f"user{idx}@example.com"
    username = f"user{idx}"
    password = "password123"

    r_reg = client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert r_reg.status_code == 201, r_reg.text

    r_login = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r_login.status_code == 200, r_login.text
    token = r_login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_wish_requires_auth(client: TestClient) -> None:
    resp = client.post(
        "/wishes",
        json={
            "title": "Test wish",
            "link": "",
            "price_estimate": "100.00",
            "notes": "",
        },
    )
    assert resp.status_code == 401
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "http_error"


def test_create_and_get_wish(client: TestClient) -> None:
    headers = register_and_login(client, idx=1)

    payload = {
        "title": "Steam Deck",
        "link": "https://store.steampowered.com/",
        "price_estimate": "399.99",
        "notes": "Игры",
    }

    r_create = client.post("/wishes", json=payload, headers=headers)
    assert r_create.status_code == 201, r_create.text
    created = r_create.json()
    wish_id = created["id"]
    assert created["title"] == payload["title"]
    assert created["owner_id"] > 0

    r_get = client.get(f"/wishes/{wish_id}", headers=headers)
    assert r_get.status_code == 200
    got = r_get.json()
    assert got["id"] == wish_id
    assert got["title"] == payload["title"]


def test_wishes_pagination_and_owner_only(client: TestClient) -> None:
    headers_user1 = register_and_login(client, idx=1)
    headers_user2 = register_and_login(client, idx=2)

    prices_user1 = ["10.00", "20.00", "30.00"]
    for p in prices_user1:
        r = client.post(
            "/wishes",
            json={
                "title": f"u1-{p}",
                "link": "",
                "price_estimate": p,
                "notes": "",
            },
            headers=headers_user1,
        )
        assert r.status_code == 201

    prices_user2 = ["100.00", "200.00"]
    for p in prices_user2:
        r = client.post(
            "/wishes",
            json={
                "title": f"u2-{p}",
                "link": "",
                "price_estimate": p,
                "notes": "",
            },
            headers=headers_user2,
        )
        assert r.status_code == 201

    r_page1 = client.get("/wishes?limit=2&offset=0", headers=headers_user1)
    assert r_page1.status_code == 200
    data1 = r_page1.json()
    assert data1["limit"] == 2
    assert data1["offset"] == 0
    assert data1["total"] == 3
    assert len(data1["items"]) == 2
    for w in data1["items"]:
        assert w["owner_id"] != 0

    r_page2 = client.get("/wishes?limit=2&offset=2", headers=headers_user1)
    assert r_page2.status_code == 200
    data2 = r_page2.json()
    assert data2["limit"] == 2
    assert data2["offset"] == 2
    assert data2["total"] == 3
    assert len(data2["items"]) == 1

    r_user2 = client.get("/wishes?limit=10&offset=0", headers=headers_user2)
    assert r_user2.status_code == 200
    data_u2 = r_user2.json()
    assert data_u2["total"] == 2
    assert len(data_u2["items"]) == 2
    for w in data_u2["items"]:
        assert w["owner_id"] != 0


def test_price_filter(client: TestClient) -> None:
    headers = register_and_login(client, idx=1)

    prices = ["10.00", "50.00", "200.00"]
    for p in prices:
        r = client.post(
            "/wishes",
            json={
                "title": f"item-{p}",
                "link": "",
                "price_estimate": p,
                "notes": "",
            },
            headers=headers,
        )
        assert r.status_code == 201

    r = client.get("/wishes?limit=10&offset=0&price_lt=100.00", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 2
    returned_prices = sorted(Decimal(w["price_estimate"]) for w in data["items"])
    assert returned_prices == [Decimal("10.00"), Decimal("50.00")]


def test_owner_only_access_forbidden(client: TestClient) -> None:
    headers1 = register_and_login(client, idx=1)
    headers2 = register_and_login(client, idx=2)

    r_create = client.post(
        "/wishes",
        json={
            "title": "Secret wish",
            "link": "",
            "price_estimate": "100.00",
            "notes": "",
        },
        headers=headers1,
    )
    assert r_create.status_code == 201
    wish_id = r_create.json()["id"]

    r_forbidden = client.get(f"/wishes/{wish_id}", headers=headers2)
    assert r_forbidden.status_code == 403
    body = r_forbidden.json()
    assert "error" in body
    assert body["error"]["code"] == "forbidden"


def test_negative_price_rejected(client: TestClient) -> None:
    headers = register_and_login(client, idx=1)

    r = client.post(
        "/wishes",
        json={
            "title": "Bad wish",
            "link": "",
            "price_estimate": "-1.00",
            "notes": "",
        },
        headers=headers,
    )
    assert r.status_code == 422
