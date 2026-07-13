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


def test_packet_has_the_three_file_skeleton(woven: Path):
    for rel in ("package.json", "manifest.json", "src/client.js", "src/index.js", "bin/cli.js"):
        assert (woven / "mcp-packet" / rel).exists(), rel


def test_packet_manifest_is_byte_faithful(woven: Path):
    embedded = json.loads((woven / "mcp-packet" / "manifest.json").read_text())
    assert embedded == _manifest()
    assert len(embedded["tools"]) == 24  # Talk's frozen floor


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
    assert "TOOL_COUNT = 24" in src


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
    # The 8 gap knobs must NOT appear as callable tools — a packet that offers
    # apply_update and 404s mid-incident is worse than one that omits it.
    names = {t["name"] for t in _word_manifest()["tools"]}
    for gap in ("get_logs", "run_selftest", "apply_update", "reset_to_defaults",
                "enter_safe_mode", "exit_safe_mode", "reconnect", "get_capabilities"):
        assert gap not in names, f"{gap} is a documented gap, must not be advertised"


def test_ept_auth_variant_emits_ept_headers():
    cloud_weave = dict(
        TALK_WEAVE,
        product="windy-mind",
        **{"class": "cloud"},
        http={"base_default": "https://api.windymind.ai/ops", "base_env": "WINDY_MIND_OPS_URL"},
        auth={"kind": "ept", "token_env": "WINDY_EPT"},
        package={"name": "windy-mind-mcp", "version": "0.0.0-loom-test"},
    )
    packet = emit_mcp_packet(_manifest(), cloud_weave)
    assert "WINDY_EPT" in packet["src/client.js"]
    assert "readFileSync" not in packet["src/client.js"].split("const BASE")[0].split("// EPT auth")[1]
    twin = emit_python_twin(_manifest(), cloud_weave)
    assert "WINDY_EPT" in twin
