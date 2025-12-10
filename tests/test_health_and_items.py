from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_items_not_found(client: TestClient) -> None:
    resp = client.get("/items/999")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "not_found"


def test_items_validation_error(client: TestClient) -> None:
    resp = client.post("/items", params={"name": ""})
    assert resp.status_code == 422
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "validation_error"


def test_items_create_ok(client: TestClient) -> None:
    resp = client.post("/items", params={"name": "test-item"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["name"] == "test-item"

    resp2 = client.post("/items", params={"name": "second"})
    data2 = resp2.json()
    assert data2["id"] == 2
