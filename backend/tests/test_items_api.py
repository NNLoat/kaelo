"""Integration / API-contract tests for the items endpoints.

These run against a real postgres:17 (via testcontainers), driving the actual
FastAPI app through its HTTP layer with TestClient.
"""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_items_empty(client: TestClient) -> None:
    resp = client.get("/api/items")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_item(client: TestClient) -> None:
    resp = client.post(
        "/api/items",
        json={"name": "widget", "description": "a thing"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["name"] == "widget"
    assert body["description"] == "a thing"
    assert "created_at" in body


def test_create_item_without_description(client: TestClient) -> None:
    resp = client.post("/api/items", json={"name": "no-desc"})
    assert resp.status_code == 201
    assert resp.json()["description"] is None


def test_create_item_validation_error(client: TestClient) -> None:
    # name is required and must be non-empty (min_length=1).
    resp = client.post("/api/items", json={"name": ""})
    assert resp.status_code == 422


def test_get_item_round_trip(client: TestClient) -> None:
    created = client.post("/api/items", json={"name": "fetch-me"}).json()
    resp = client.get(f"/api/items/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "fetch-me"


def test_get_missing_item_returns_404(client: TestClient) -> None:
    resp = client.get("/api/items/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Item not found"


def test_delete_item(client: TestClient) -> None:
    created = client.post("/api/items", json={"name": "delete-me"}).json()
    del_resp = client.delete(f"/api/items/{created['id']}")
    assert del_resp.status_code == 204

    # Now gone.
    assert client.get(f"/api/items/{created['id']}").status_code == 404


def test_delete_missing_item_returns_404(client: TestClient) -> None:
    resp = client.delete("/api/items/999999")
    assert resp.status_code == 404


def test_list_reflects_creates(client: TestClient) -> None:
    client.post("/api/items", json={"name": "a"})
    client.post("/api/items", json={"name": "b"})
    names = [item["name"] for item in client.get("/api/items").json()]
    assert names == ["a", "b"]


def test_isolation_between_tests(client: TestClient) -> None:
    # Proves the rollback fixture works: despite other tests creating rows,
    # each test starts from an empty table.
    assert client.get("/api/items").json() == []
