"""Canonical ops-hook tests — full HTTP fidelity, injected runner/prober.

The hook is the fleet-generic doctor (ops-hook/hook.py); platforms vendor
it verbatim with a drift test. These tests pin: the three-layer wall
(token, confirm nonce, single-op 409), env-driven compose invocation +
allowlist, injection-proof atomic env editing with restore, redeploy's
last-known-good rollback + sha attestation, optional migrations, and the
`passed`-not-`ok` envelope rule.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

TOKEN = "test-hook-token"
os.environ["OPS_HOOK_TOKEN"] = TOKEN
os.environ["OPS_HOOK_PRODUCT"] = "windy-testproduct"
os.environ["OPS_HOOK_COMPOSE_CMD"] = "docker compose -p testproj --env-file .env.production"
os.environ["OPS_HOOK_SERVICE"] = "test-api"
os.environ["OPS_HOOK_IMAGE_REF"] = "windy-test-api:local"
os.environ["OPS_HOOK_CONFIG_ALLOWLIST"] = "BRAVE_SEARCH_API_KEY,LOG_LEVEL"
os.environ["OPS_HOOK_GATE_ATTEMPTS"] = "3"
os.environ["OPS_HOOK_GATE_INTERVAL"] = "0.01"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ops-hook"))
import hook as hook_module  # noqa: E402
from hook import OpsHook, make_handler  # noqa: E402


class FakeRunner:
    def __init__(self):
        self.calls: list[list[str]] = []
        self.fail_prefixes: list[list[str]] = []

    def __call__(self, cmd, timeout=600.0):
        self.calls.append(list(cmd))
        for prefix in self.fail_prefixes:
            if cmd[: len(prefix)] == prefix:
                return 1, "boom"
        return 0, "ok"


class FakePatient:
    def __init__(self):
        self.health_status = 200
        self.commit_sha = "abc1234def"

    def __call__(self, url, timeout=3.0):
        if url.endswith("/health"):
            if self.health_status is None:
                raise ConnectionError("refused")
            return self.health_status, b"{}"
        if url.endswith("/version"):
            return 200, json.dumps({"commit_sha": self.commit_sha}).encode()
        raise AssertionError(f"unexpected probe {url}")


@pytest.fixture()
def env_file(tmp_path, monkeypatch):
    path = tmp_path / ".env.production"
    path.write_text("BRAVE_SEARCH_API_KEY=old-brave\nDATABASE_URL=postgres://x\n")
    monkeypatch.setattr(hook_module, "ENV_FILE", str(path))
    return path


@pytest.fixture()
def rig(env_file):
    runner, patient = FakeRunner(), FakePatient()
    hook = OpsHook(runner=runner, http_get=patient)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(hook))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    yield {"base": base, "runner": runner, "patient": patient, "hook": hook, "env": env_file}
    server.shutdown()


def _call(base, method, path, body=None, token=TOKEN):
    req = urllib.request.Request(
        base + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"content-type": "application/json"}
        | ({"authorization": f"Bearer {token}"} if token else {}),
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _nonce(base):
    status, body = _call(base, "POST", "/hook/confirm")
    assert status == 200
    return body["nonce"]


def test_health_open_everything_else_walled(rig):
    status, body = _call(rig["base"], "GET", "/hook/health", token=None)
    assert status == 200 and body["service"] == "windy-testproduct-ops-hook"
    for method, path in [("GET", "/hook/config"), ("POST", "/hook/confirm"),
                         ("POST", "/hook/restart"), ("POST", "/hook/redeploy"),
                         ("POST", "/hook/config")]:
        status, body = _call(rig["base"], method, path, body={}, token=None)
        assert status == 401 and "OPS_HOOK_TOKEN" in body["remediation"], path


def test_mutations_require_single_use_nonce(rig):
    base = rig["base"]
    status, body = _call(base, "POST", "/hook/restart", body={})
    assert status == 428 and body["error"] == "confirm_required"
    nonce = _nonce(base)
    status, body = _call(base, "POST", "/hook/restart", body={"nonce": nonce})
    assert status == 200 and body["passed"] is True
    status, _ = _call(base, "POST", "/hook/restart", body={"nonce": nonce})
    assert status == 428, "replay refused"


def test_busy_lock_409(rig):
    base = rig["base"]
    assert rig["hook"]._op_lock.acquire(blocking=False)
    try:
        status, body = _call(base, "POST", "/hook/restart", body={"nonce": _nonce(base)})
        assert status == 409 and body["error"] == "operation_in_progress"
    finally:
        rig["hook"]._op_lock.release()


def test_compose_cmd_is_env_driven(rig):
    base = rig["base"]
    _call(base, "POST", "/hook/restart", body={"nonce": _nonce(base)})
    restart_call = next(c for c in rig["runner"].calls if "restart" in c)
    assert restart_call[:6] == [
        "docker", "compose", "-p", "testproj", "--env-file", ".env.production"
    ], "the SUBSTRATE-documented compose invocation is used verbatim"
    assert restart_call[-1] == "test-api"


def test_redeploy_happy_path_no_migrations_by_default(rig):
    base = rig["base"]
    status, body = _call(base, "POST", "/hook/redeploy",
                         body={"nonce": _nonce(base), "expected_commit_sha": "abc1234"})
    assert body["passed"] is True
    names = [s["name"] for s in body["stages"]]
    assert names == ["snapshot_last_good", "build", "up", "health_gate"], \
        "no migrations stage when OPS_HOOK_MIGRATE_CMD is unset (stateless services)"
    flat = [" ".join(c) for c in rig["runner"].calls]
    assert any(c == "docker tag windy-test-api:local windy-test-api:last-good" for c in flat)


def test_redeploy_pull_mode(rig, monkeypatch):
    monkeypatch.setattr(hook_module, "BUILD_MODE", "pull")
    base = rig["base"]
    status, body = _call(base, "POST", "/hook/redeploy", body={"nonce": _nonce(base)})
    names = [s["name"] for s in body["stages"]]
    assert "pull" in names and "build" not in names, "pull mode fetches, never builds"
    assert any(c[-2:] == ["pull", "test-api"] for c in rig["runner"].calls)


def test_redeploy_migrate_cmd_optional(rig, monkeypatch):
    monkeypatch.setattr(hook_module, "MIGRATE_CMD", ["alembic", "upgrade", "head"])
    base = rig["base"]
    status, body = _call(base, "POST", "/hook/redeploy", body={"nonce": _nonce(base)})
    assert "migrations" in [s["name"] for s in body["stages"]]
    assert any("alembic upgrade head" in " ".join(c) for c in rig["runner"].calls)


def test_redeploy_sha_mismatch_rolls_back(rig):
    base = rig["base"]
    rig["patient"].commit_sha = "wrong000"
    status, body = _call(base, "POST", "/hook/redeploy",
                         body={"nonce": _nonce(base), "expected_commit_sha": "abc1234"})
    assert body["passed"] is False
    by_name = {s["name"]: s for s in body["stages"]}
    assert by_name["health_gate"]["detail"] == "sha_mismatch"
    assert "rollback_last_good" in by_name
    assert any("--force-recreate" in " ".join(c) for c in rig["runner"].calls)


def test_redeploy_dead_gate_rolls_back_and_regates(rig):
    base = rig["base"]
    patient = rig["patient"]
    patient.health_status = None
    original = rig["runner"]

    class ReviveOnRollback(FakeRunner):
        def __call__(self, cmd, timeout=600.0):
            rc = original(cmd, timeout)
            if "--force-recreate" in cmd:
                patient.health_status = 200
            return rc

    rig["hook"].runner = ReviveOnRollback()
    status, body = _call(base, "POST", "/hook/redeploy", body={"nonce": _nonce(base)})
    assert body["passed"] is False, "a rolled-back redeploy is still a FAILED redeploy"
    assert {s["name"]: s for s in body["stages"]}["rollback_last_good"]["ok"] is True


def test_config_view_booleans_only(rig):
    status, body = _call(rig["base"], "GET", "/hook/config")
    assert body["settable"] == {"BRAVE_SEARCH_API_KEY": True, "LOG_LEVEL": False}
    assert "old-brave" not in json.dumps(body)


def test_config_set_allowlisted_key(rig):
    base = rig["base"]
    status, body = _call(base, "POST", "/hook/config",
                         body={"nonce": _nonce(base), "key": "BRAVE_SEARCH_API_KEY", "value": "new-brave"})
    assert body["passed"] is True
    content = rig["env"].read_text()
    assert "BRAVE_SEARCH_API_KEY=new-brave" in content
    assert "DATABASE_URL=postgres://x" in content
    assert any("--force-recreate" in " ".join(c) for c in rig["runner"].calls), \
        "recreate, not restart — compose restart skips env_file"


def test_config_rejects_non_allowlisted_and_injection(rig):
    base = rig["base"]
    status, body = _call(base, "POST", "/hook/config",
                         body={"nonce": _nonce(base), "key": "DATABASE_URL", "value": "x"})
    assert body["passed"] is False and body["stages"][0]["name"] == "allowlist"
    status, body = _call(base, "POST", "/hook/config",
                         body={"nonce": _nonce(base), "key": "BRAVE_SEARCH_API_KEY",
                               "value": "evil\nDATABASE_URL=hacked"})
    assert body["passed"] is False and body["stages"][0]["name"] == "validate"
    assert "hacked" not in rig["env"].read_text()


def test_config_failed_gate_restores_env(rig):
    base = rig["base"]
    rig["patient"].health_status = None
    status, body = _call(base, "POST", "/hook/config",
                         body={"nonce": _nonce(base), "key": "BRAVE_SEARCH_API_KEY", "value": "bad"})
    assert body["passed"] is False
    assert "BRAVE_SEARCH_API_KEY=old-brave" in rig["env"].read_text()
