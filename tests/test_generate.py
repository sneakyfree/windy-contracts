"""Loom generator tests — weave Talk's frozen rev.6 and prove the cloth.

Gates: outputs parse/compile (node --check for JS, compile() for Python),
the embedded manifest is byte-faithful, band floors follow the mapping
table, determinism holds (same inputs → byte-identical outputs), and the
conformance driver's static gate actually catches drift.
"""

from __future__ import annotations

import json
import py_compile
import shutil
import subprocess
from pathlib import Path

import pytest

from loom.generate import emit_mcp_packet, emit_python_twin, validate_weave, weave

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "schema" / "fixtures" / "windytalk"

TALK_WEAVE = {
    "product": "windy-talk",
    "class": "desktop",
    "http": {"base_default": "http://127.0.0.1:8782", "base_env": "WINDY_TALK_CONTROL_URL"},
    "auth": {
        "kind": "install_token",
        "token_path_default": "~/.windytalk/control.token",
        "token_env": "WINDYTALK_CONTROL_TOKEN",
        "token_path_env": "WINDYTALK_CONTROL_TOKEN_PATH",
    },
    "package": {"name": "windy-talk-mcp", "version": "0.0.0-loom-test"},
}


def _manifest() -> dict:
    return json.loads((FIXTURES / "control.mcp.v1.json").read_text())


@pytest.fixture(scope="module")
def woven(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("woven")
    wv = out / "weave.json"
    wv.write_text(json.dumps(TALK_WEAVE))
    weave(FIXTURES / "control.mcp.v1.json", wv, out)
    return out


def test_weave_config_schema_accepts_talk_and_rejects_junk():
    assert validate_weave(TALK_WEAVE) == []
    assert validate_weave({"product": "x"})  # missing required keys
    bad = dict(TALK_WEAVE, auth={"kind": "vibes"})
    assert any("vibes" in e for e in validate_weave(bad))


def test_packet_has_the_skeleton(woven: Path):
    for rel in ("package.json", "manifest.json", "src/client.js", "src/server.js", "src/index.js", "bin/cli.js"):
        assert (woven / "mcp-packet" / rel).exists(), rel


def test_desktop_packet_has_no_http_entrypoint(woven: Path):
    # Class D is stdio-only; the remote entrypoint is a cloud-class artifact.
    assert not (woven / "mcp-packet" / "src" / "http.js").exists()


def test_packet_manifest_is_byte_faithful(woven: Path):
    embedded = json.loads((woven / "mcp-packet" / "manifest.json").read_text())
    assert embedded == _manifest()
    assert len(embedded["tools"]) == len(_manifest()["tools"])  # byte-faithful to source


@pytest.mark.skipif(shutil.which("node") is None, reason="node not on PATH")
def test_generated_js_parses(woven: Path):
    for rel in ("src/client.js", "src/index.js", "bin/cli.js"):
        subprocess.run(
            ["node", "--check", str(woven / "mcp-packet" / rel)],
            check=True, capture_output=True,
        )


def test_generated_python_twin_compiles(woven: Path):
    py_compile.compile(str(woven / "windy_talk_twin.py"), doraise=True)


def test_generated_conformance_driver_compiles(woven: Path):
    py_compile.compile(str(woven / "conformance_driver.py"), doraise=True)


def test_twin_registers_every_tool_with_band_floors(woven: Path):
    src = (woven / "windy_talk_twin.py").read_text()
    manifest = _manifest()
    mapping = json.loads((ROOT / "schema" / "band-ei-mapping.v1.json").read_text())
    floors = {k: v for k, v in mapping["band_floor_defaults"].items() if not k.startswith("$")}
    for t in manifest["tools"]:
        assert f'"{t["name"]}"' in src
        expected_band = t.get("band_floor", floors[t["tier"]])
        # every entry line carries its band
        line = next(l for l in src.splitlines() if f'_cap(registry, "{t["name"]}"' in l)
        assert f'band="{expected_band}"' in line
    assert f"TOOL_COUNT = {len(_manifest()['tools'])}" in src


def test_deterministic_weave(tmp_path):
    wv = tmp_path / "weave.json"
    wv.write_text(json.dumps(TALK_WEAVE))
    a, b = tmp_path / "a", tmp_path / "b"
    weave(FIXTURES / "control.mcp.v1.json", wv, a)
    weave(FIXTURES / "control.mcp.v1.json", wv, b)
    for fa in sorted(a.rglob("*")):
        if fa.is_file():
            fb = b / fa.relative_to(a)
            assert fa.read_bytes() == fb.read_bytes(), f"nondeterministic: {fa.name}"


def test_conformance_static_gate_catches_drift(woven: Path, tmp_path):
    driver = woven / "conformance_driver.py"
    # Pristine: static gate passes (live gate skips — no surface running).
    ok = subprocess.run(
        ["python3", str(driver)], capture_output=True, text=True, cwd=woven,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "static OK" in ok.stdout

    # Tamper with the packet manifest → static gate must fail.
    drifted = tmp_path / "drifted"
    shutil.copytree(woven, drifted)
    pm = drifted / "manifest.json"
    m = json.loads(pm.read_text())
    m["tools"][0]["description"] += " (hand-edited)"
    pm.write_text(json.dumps(m, indent=2) + "\n")
    bad = subprocess.run(
        ["python3", str(drifted / "conformance_driver.py")],
        capture_output=True, text=True, cwd=drifted,
    )
    assert bad.returncode != 0
    assert "differs from source" in bad.stdout


def test_refuses_to_weave_an_invalid_manifest(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"contract": "control.mcp.v1", "tools": [
        {"name": "x", "tier": "yolo", "description": "d" * 50, "inputSchema": {}}
    ]}))
    wv = tmp_path / "weave.json"
    wv.write_text(json.dumps(TALK_WEAVE))
    with pytest.raises(ValueError, match="refusing to weave"):
        weave(bad, wv, tmp_path / "out")


WORD_WEAVE = {
    "product": "windy-word",
    "class": "desktop",
    "http": {"base_default": "http://127.0.0.1:18765", "base_env": "WINDY_WORD_URL"},
    "auth": {
        "kind": "install_token",
        "token_path_default": "~/.windy-word/control.token",
        "token_env": "WINDY_WORD_CONTROL_TOKEN",
        "token_path_env": "WINDY_WORD_CONTROL_TOKEN_PATH",
    },
    "package": {"name": "windy-word-mcp", "version": "0.0.0-loom-test"},
}


def _word_manifest() -> dict:
    return json.loads(
        (ROOT / "schema" / "fixtures" / "windy-word" / "control.mcp.v1.json").read_text()
    )


@pytest.fixture(scope="module")
def word_woven(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("word")
    wv = out / "weave.json"
    wv.write_text(json.dumps(WORD_WEAVE))
    weave(ROOT / "schema" / "fixtures" / "windy-word" / "control.mcp.v1.json", wv, out)
    return out


def test_word_manifest_is_gen1_bound_and_valid():
    from loom.validate import validate_manifest

    m = _word_manifest()
    r = validate_manifest(m)
    assert r.ok, r.errors
    # Every Word tool is a real route (Gen-1 escape hatch) — none falls back
    # to the phantom /invoke Word doesn't serve.
    assert all("transport" in t for t in m["tools"]), "a Word tool lacks its route binding"


def test_word_client_builds_a_route_table(word_woven: Path):
    client = (word_woven / "mcp-packet" / "src" / "client.js").read_text()
    assert "buildRouteTable" in client
    # spot-check the three routing modes are all reachable in the generated code
    assert "route.method === 'GET'" in client
    assert "route.argMapping === 'none'" in client
    assert "new URLSearchParams" in client


def test_woven_packet_is_sovereign_override_aware(word_woven: Path):
    # ADR-062: the Loom generates the co-sign path so platforms inherit it.
    # All three emitted surfaces must PRESERVE + legibly surface an
    # `override_required` response instead of flattening it to an error.
    client = (word_woven / "mcp-packet" / "src" / "client.js").read_text()
    server = (word_woven / "mcp-packet" / "src" / "server.js").read_text()
    twin = (word_woven / "windy_word_twin.py").read_text()
    # client preserves the marker verbatim (doesn't normalize it to {ok:false})
    assert "sovereign_override_required === true" in client and "return parsed" in client
    # tools/call surfaces it as an actionable step, not a failure
    assert "OWNER APPROVAL REQUIRED" in server
    assert "sovereign_override_required === true" in server
    # the python twin preserves it too
    assert 'get("sovereign_override_required") is True' in twin


@pytest.mark.skipif(shutil.which("node") is None, reason="node not on PATH")
def test_word_generated_js_parses(word_woven: Path):
    for rel in ("src/client.js", "src/index.js"):
        subprocess.run(
            ["node", "--check", str(word_woven / "mcp-packet" / rel)],
            check=True, capture_output=True,
        )


def test_word_twin_carries_the_route_table(word_woven: Path):
    twin = (word_woven / "windy_word_twin.py").read_text()
    py_compile.compile(str(word_woven / "windy_word_twin.py"), doraise=True)
    assert '"/sound-effects/master-volume"' in twin
    assert '"/app/restart"' in twin
    assert '"arg_mapping": "none"' in twin  # restart/check-update carry it


def test_word_baseline_gaps_are_not_advertised():
    # The remaining gap knobs must NOT appear as callable tools — a packet that
    # offers apply_update and 404s mid-incident is worse than one that omits it.
    # (get_logs graduated gap→implemented 2026-07-13, windy-pro #237: it's now
    # a real route, GET /control/logs, so it IS advertised.)
    names = {t["name"] for t in _word_manifest()["tools"]}
    for shipped in ("get_logs", "get_capabilities", "run_selftest", "reconnect",
                    "enter_safe_mode", "exit_safe_mode"):
        assert shipped in names, f"{shipped} shipped (windy-pro #237-#241) — must be advertised now"
    for gap in ("apply_update", "reset_to_defaults"):
        assert gap not in names, f"{gap} is a documented gap, must not be advertised"


MIND_WEAVE = {
    "product": "windy-mind",
    "class": "cloud",
    "http": {"base_default": "https://api.windymind.ai", "base_env": "WINDY_MIND_API_URL"},
    "auth": {"kind": "ept", "token_env": "WINDY_EPT"},
    "package": {"name": "windy-mind-mcp", "version": "0.0.0-loom-test"},
}


def _mind_manifest() -> dict:
    return json.loads(
        (ROOT / "schema" / "fixtures" / "windy-mind" / "ops.mcp.v1.json").read_text()
    )


def test_ept_auth_variant_emits_ept_headers():
    packet = emit_mcp_packet(_manifest(), MIND_WEAVE)
    assert "WINDY_EPT" in packet["src/client.js"]
    assert "readFileSync" not in packet["src/client.js"].split("const BASE")[0].split("// EPT auth")[1]
    twin = emit_python_twin(_manifest(), MIND_WEAVE)
    assert "WINDY_EPT" in twin


@pytest.fixture(scope="module")
def mind_woven(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("mind")
    wv = out / "weave.json"
    wv.write_text(json.dumps(MIND_WEAVE))
    weave(ROOT / "schema" / "fixtures" / "windy-mind" / "ops.mcp.v1.json", wv, out)
    return out


def test_cloud_class_gets_streamable_http_entrypoint(mind_woven: Path):
    http = mind_woven / "mcp-packet" / "src" / "http.js"
    assert http.exists(), "cloud class must emit the remote /mcp entrypoint"
    src = http.read_text()
    assert "StreamableHTTPServerTransport" in src
    assert "/mcp" in src
    # EPT passthrough: the caller's Authorization becomes authOverride.
    assert "req.headers['authorization']" in src
    assert "authOverride" in src


@pytest.mark.skipif(shutil.which("node") is None, reason="node not on PATH")
def test_cloud_generated_js_parses(mind_woven: Path):
    for rel in ("src/client.js", "src/server.js", "src/index.js", "src/http.js"):
        subprocess.run(
            ["node", "--check", str(mind_woven / "mcp-packet" / rel)],
            check=True, capture_output=True,
        )


FLY_WEAVE = {
    "product": "windy-agent",
    "class": "agent-host",
    "server": "native",
    "auth": {"kind": "ept", "token_env": "WINDY_EPT"},
}


def test_native_server_weaves_only_the_conformance_driver(tmp_path):
    wv = tmp_path / "weave.json"
    wv.write_text(json.dumps(FLY_WEAVE))
    out = tmp_path / "out"
    written = weave(
        ROOT / "schema" / "fixtures" / "windy-agent" / "control.mcp.v1.json", wv, out
    )
    # No JS packet, no Python twin — the platform owns its native server.
    assert not (out / "mcp-packet").exists()
    assert not list(out.glob("*_twin.py"))
    assert (out / "conformance_driver.py").exists()
    assert (out / "manifest.json").exists()


def test_native_conformance_driver_static_gate_runs(tmp_path):
    wv = tmp_path / "weave.json"
    wv.write_text(json.dumps(FLY_WEAVE))
    out = tmp_path / "out"
    weave(ROOT / "schema" / "fixtures" / "windy-agent" / "control.mcp.v1.json", wv, out)
    r = subprocess.run(
        ["python3", str(out / "conformance_driver.py")],
        capture_output=True, text=True, cwd=out,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "static OK" in r.stdout
    assert "native server" in r.stdout  # live gate skipped, not HTTP-probed


def test_native_weave_config_needs_no_http_or_package():
    from loom.generate import validate_weave

    assert validate_weave(FLY_WEAVE) == []
    # a woven config still must carry http/auth/package
    assert validate_weave({"product": "x", "class": "cloud"})


def test_ops_contract_is_a_healing_surface(mind_woven: Path):
    # The Mind ops shim carries the baseline (Class C control surface), and
    # its implemented tools bind to real api.windymind.ai routes.
    m = _mind_manifest()
    assert m["contract"].startswith("ops.")
    assert all("transport" in t for t in m["tools"])
    # remote-only EPT: no token file reads leak into the client
    packet = emit_mcp_packet(m, MIND_WEAVE)
    assert "control.token" not in packet["src/client.js"]


def test_search_procession_validates_and_weaves_cloud(tmp_path):
    # Procession replication: Search is Class C like Mind — validates clean
    # and weaves the remote http.js. No new mechanism, just a new manifest.
    from loom.validate import validate_manifest

    fx = ROOT / "schema" / "fixtures" / "windy-search" / "ops.mcp.v1.json"
    m = json.loads(fx.read_text())
    assert validate_manifest(m).ok
    assert all("transport" in t for t in m["tools"])
    wv = tmp_path / "weave.json"
    wv.write_text(json.dumps(dict(MIND_WEAVE, product="windy-search",
        http={"base_default": "https://api.windysearch.com", "base_env": "WINDY_SEARCH_API_URL"},
        package={"name": "windy-search-mcp", "version": "0.0.0-loom-test"})))
    out = tmp_path / "out"
    weave(fx, wv, out)
    assert (out / "mcp-packet" / "src" / "http.js").exists()  # cloud → remote entrypoint


def test_mail_procession_validates_and_weaves_cloud(tmp_path):
    from loom.validate import validate_manifest
    fx = ROOT / "schema" / "fixtures" / "windy-mail" / "ops.mcp.v1.json"
    m = json.loads(fx.read_text())
    r = validate_manifest(m)
    assert r.ok, r.errors
    # Mail exercises a per-tool band_floor (get_stats is TRUSTED, admin-read)
    stats = next(t for t in m["tools"] if t["name"] == "get_stats")
    assert stats["band_floor"] == "TRUSTED"
    wv = tmp_path / "weave.json"
    wv.write_text(json.dumps(dict(MIND_WEAVE, product="windy-mail",
        http={"base_default": "https://mail.windymail.ai", "base_env": "WINDY_MAIL_API_URL"},
        package={"name": "windy-mail-mcp", "version": "0.0.0-loom-test"})))
    out = tmp_path / "out"
    weave(fx, wv, out)
    assert (out / "mcp-packet" / "src" / "http.js").exists()
    # the TRUSTED band floor rides into the generated Python twin
    twin = (out / "windy_mail_twin.py").read_text()
    assert "TRUSTED" in twin


def test_chat_procession_multiservice(tmp_path):
    # Chat is a multi-service constellation. The fleet-health aggregator
    # (windy-chat #143, 2026-07-13) closed the headline gap: one endpoint
    # serves get_health + get_status + get_capabilities at once.
    from loom.validate import validate_manifest
    fx = ROOT / "schema" / "fixtures" / "windy-chat" / "ops.mcp.v1.json"
    m = json.loads(fx.read_text())
    assert validate_manifest(m).ok
    assert len(m["tools"]) == 4  # the aggregator triad + check_for_update
    names = {t["name"] for t in m["tools"]}
    assert names == {"get_health", "get_status", "get_capabilities", "check_for_update"}
    # the triad binds to the ONE aggregator route (MULTI-SERVICE-OPS pattern);
    # check_for_update (Steamroller, 2026-07-13) is the one non-aggregator tool.
    triad = {t["transport"]["path"] for t in m["tools"] if t["name"] != "check_for_update"}
    assert triad == {"/api/v1/ops/health"}
    assert "$headline_gap" in m and "CLOSED" in m["$headline_gap"]
    wv = tmp_path / "weave.json"
    wv.write_text(json.dumps(dict(MIND_WEAVE, product="windy-chat",
        http={"base_default": "https://chat.windychat.ai", "base_env": "WINDY_CHAT_API_URL"},
        package={"name": "windy-chat-mcp", "version": "0.0.0-loom-test"})))
    out = tmp_path / "out"
    weave(fx, wv, out)
    assert (out / "mcp-packet" / "src" / "http.js").exists()
