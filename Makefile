# windy-contracts — local gates ARE the gates (GitHub Actions billing-locked).
# `make check` must be green before any merge, per ADR-060 §3.7.

.PHONY: check test validate

check: test validate

test:
	uv run pytest -q

# First citizens must stay valid forever; --strict is NOT used here because
# rev.6 predates the doctrine headers (that ramp closes at manifest v2).
validate:
	uv run python -m loom.validate schema/fixtures/windytalk/control.mcp.v1.json schema/fixtures/windytalk/hands.mcp.v1.json schema/fixtures/windy-word/control.mcp.v1.json schema/fixtures/windy-mind/ops.mcp.v1.json schema/fixtures/windy-agent/control.mcp.v1.json schema/fixtures/windy-search/ops.mcp.v1.json schema/fixtures/windy-mail/ops.mcp.v1.json schema/fixtures/windy-chat/ops.mcp.v1.json schema/fixtures/windy-clone/ops.mcp.v1.json schema/fixtures/windy-registry/ops.mcp.v1.json schema/fixtures/windy-translate/ops.mcp.v1.json schema/fixtures/windy-admin/ops.mcp.v1.json
