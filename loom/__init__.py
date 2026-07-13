"""The Loom — ADR-060 L1.

Validates (and, as L1 progresses, generates) every Windy platform's
bilingual agent-control surface from its manifest. The manifest is the
single generative source of truth; both transports and the conformance
driver are woven from it so they cannot drift.
"""

from loom.validate import validate_manifest  # noqa: F401
