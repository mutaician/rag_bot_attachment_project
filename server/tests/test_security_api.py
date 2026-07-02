"""API regression tests for P0 authorization fixes."""

import json
import io

import pytest
from fastapi.testclient import TestClient

from app import db
from app.auth.passwords import hash_password
from app.auth.rate_limit import reset_all_rate_limits
from app.main import app


def _login(username: str, password: str) -> TestClient:
    client = TestClient(app)
    res = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return client


def _conversation_id_from_sse(body: str) -> str:
    for line in body.splitlines():
        if line.startswith("data:") and '"conversation_id"' in line:
            return json.loads(line.removeprefix("data:").strip())["conversation_id"]
    raise AssertionError("conversation_id not found in SSE response")


@pytest.fixture(scope="module", autouse=True)
def ensure_test_users() -> None:
    for username, display, password in (
        ("sec_test_a", "Sec Test A", "pass-a"),
        ("sec_test_b", "Sec Test B", "pass-b"),
    ):
        if db.get_user_by_username(username) is None:
            db.create_user(username, display, hash_password(password))


@pytest.fixture(autouse=True)
def clear_rate_limits() -> None:
    reset_all_rate_limits()


def test_private_conversation_hidden_from_other_user() -> None:
    a = _login("sec_test_a", "pass-a")
    b = _login("sec_test_b", "pass-b")

    res = a.post(
        "/chat",
        json={"message": "private secret thread", "visibility": "private"},
    )
    assert res.status_code == 200
    conv_id = _conversation_id_from_sse(res.text)

    list_b = b.get("/conversations")
    assert list_b.status_code == 200
    assert conv_id not in {c["id"] for c in list_b.json()}

    get_b = b.get(f"/conversations/{conv_id}")
    assert get_b.status_code == 404


def test_team_conversation_visible_but_not_deletable_by_other() -> None:
    a = _login("sec_test_a", "pass-a")
    b = _login("sec_test_b", "pass-b")

    res = a.post(
        "/chat",
        json={"message": "team visible thread", "visibility": "team"},
    )
    assert res.status_code == 200
    conv_id = _conversation_id_from_sse(res.text)

    get_b = b.get(f"/conversations/{conv_id}")
    assert get_b.status_code == 200

    delete_b = b.delete(f"/conversations/{conv_id}")
    assert delete_b.status_code == 403


def test_document_delete_restricted_to_owner() -> None:
    a = _login("sec_test_a", "pass-a")
    b = _login("sec_test_b", "pass-b")

    upload = a.post(
        "/documents/upload",
        files={"files": ("owned.txt", io.BytesIO(b"owned by a"), "text/plain")},
    )
    assert upload.status_code == 200
    doc_id = upload.json()["document_ids"][0]

    delete_b = b.delete(f"/documents/{doc_id}")
    assert delete_b.status_code == 403

    list_b = b.get("/documents")
    doc = next(d for d in list_b.json() if d["id"] == doc_id)
    assert doc["can_delete"] is False


def test_login_rate_limit() -> None:
    fresh = TestClient(app)
    for _ in range(5):
        res = fresh.post(
            "/auth/login",
            json={"username": "sec_test_a", "password": "wrong"},
        )
        assert res.status_code == 401

    blocked = fresh.post(
        "/auth/login",
        json={"username": "sec_test_a", "password": "wrong"},
    )
    assert blocked.status_code == 429
