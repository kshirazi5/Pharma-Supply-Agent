import importlib
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def load_auth(monkeypatch, **env):
    for key in ("SECRET_KEY", "ADMIN_PASSWORD", "MANAGER_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)
    sys.modules.pop("api.auth", None)
    return importlib.import_module("api.auth")


def test_refuses_to_start_without_secrets(monkeypatch):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        load_auth(monkeypatch)


def test_login_accepts_correct_and_rejects_wrong_password(monkeypatch):
    auth = load_auth(monkeypatch, SECRET_KEY="k" * 32, ADMIN_PASSWORD="pw1", MANAGER_PASSWORD="pw2")
    app = FastAPI()
    app.include_router(auth.router)
    client = TestClient(app)

    ok = client.post("/api/auth/token", data={"username": "admin", "password": "pw1"})
    assert ok.status_code == 200 and "access_token" in ok.json()

    bad = client.post("/api/auth/token", data={"username": "admin", "password": "wrong"})
    assert bad.status_code == 401


def test_token_carries_role(monkeypatch):
    auth = load_auth(monkeypatch, SECRET_KEY="k" * 32, ADMIN_PASSWORD="pw1", MANAGER_PASSWORD="pw2")
    token = auth.create_access_token({"sub": "manager", "role": "manager"})
    assert auth.get_current_user(token)["role"] == "manager"


def test_only_managers_can_approve(monkeypatch):
    load_auth(monkeypatch, SECRET_KEY="k" * 32, ADMIN_PASSWORD="pw1", MANAGER_PASSWORD="pw2")
    # Stub the database client: the role check must reject before any DB call
    import types
    fake_db = types.ModuleType("db.supabase_client")
    fake_db.get_client = lambda: pytest.fail("database should not be reached")
    monkeypatch.setitem(sys.modules, "db.supabase_client", fake_db)
    sys.modules.pop("api.approvals", None)
    approvals = importlib.import_module("api.approvals")
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        approvals.action_approval(1, approvals.ApprovalAction(action="approve"),
                                  current_user={"username": "admin", "role": "admin"})
    assert exc.value.status_code == 403
