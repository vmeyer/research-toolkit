"""Tests for the platform capability adapter + preflight gate.

These encode the acceptance criteria from the Copilot-CLI capability bug:
- the probe succeeds under Claude Code and Copilot CLI (with a web tool),
- researcher/verifier get web-search AND web-fetch on both platforms,
- a missing capability reproducibly yields BLOCKED with no artifacts,
- the current regression (Copilot registers only view/create/edit) is BLOCKED,
- URL permissions cannot rescue a missing web tool.
"""
import os
import subprocess
import sys

import pytest

from contract.capabilities import (
    ADAPTERS,
    RESEARCH_CAPABILITIES,
    WEB_FETCH,
    WEB_SEARCH,
    may_produce_artifacts,
    platforms,
    preflight,
)
from contract.validate_contract import validate_run

# Tools each harness registers when everything is wired up correctly.
CLAUDE_CODE_TOOLS = ["WebSearch", "WebFetch", "Read", "Write"]
# Copilot's native tool names (verified from the bundled SDK): web_search /
# web_fetch are native, file tools are view / create / edit.
COPILOT_WITH_WEB = ["web_search", "web_fetch", "view", "create", "edit"]
# The reported bug: the profile declared Claude tool names, Copilot dropped the
# unrecognized web names and fell back to only its default file tools.
COPILOT_REGRESSION = ["view", "create", "edit"]


# --- Probe succeeds on both platforms -------------------------------------

def test_claude_code_probe_passes():
    res = preflight("claude-code", CLAUDE_CODE_TOOLS)
    assert res.status == "PASS"
    assert res.missing == []
    assert may_produce_artifacts(res) is True


def test_copilot_probe_passes_with_web_tool():
    res = preflight("copilot-cli", COPILOT_WITH_WEB)
    assert res.status == "PASS"
    assert res.missing == []
    assert may_produce_artifacts(res) is True


@pytest.mark.parametrize(
    "platform,tools",
    [("claude-code", CLAUDE_CODE_TOOLS), ("copilot-cli", COPILOT_WITH_WEB)],
)
def test_researcher_and_verifier_get_web_search_and_fetch(platform, tools):
    # researcher-1 and verifier-1 require the same capability set.
    res = preflight(platform, tools, required=RESEARCH_CAPABILITIES)
    assert res.status == "PASS"
    assert WEB_SEARCH in res.resolved and WEB_FETCH in res.resolved


# --- The regression: Copilot sees only view/create/edit -------------------

def test_copilot_regression_is_blocked():
    res = preflight("copilot-cli", COPILOT_REGRESSION)
    assert res.status == "BLOCKED"
    # Exactly the web capabilities are missing; read/write resolve to view/edit.
    assert set(res.missing) == {WEB_SEARCH, WEB_FETCH}
    assert res.resolved["read"] == "view"
    assert res.resolved["write"] in {"edit", "create"}


def test_blocked_forbids_artifacts():
    res = preflight("copilot-cli", COPILOT_REGRESSION)
    assert may_produce_artifacts(res) is False


def test_no_artifacts_written_when_blocked(tmp_path):
    """A BLOCKED preflight must leave the output folder empty."""
    res = preflight("copilot-cli", COPILOT_REGRESSION)
    out = tmp_path / "researchers" / "sub-01"
    out.mkdir(parents=True)
    if may_produce_artifacts(res):  # guard the orchestrator must honor
        (out / "findings.md").write_text("should not happen")
    assert os.listdir(out) == []


def test_blocked_reason_is_reproducible():
    a = preflight("copilot-cli", COPILOT_REGRESSION)
    b = preflight("copilot-cli", list(COPILOT_REGRESSION))
    assert a.status == b.status == "BLOCKED"
    assert a.reason == b.reason


# --- URL permissions cannot rescue a missing web tool ---------------------

def test_copilot_native_web_tools_pass():
    # web_search / web_fetch are Copilot's native canonical names.
    res = preflight("copilot-cli", COPILOT_WITH_WEB)
    assert res.status == "PASS"
    assert res.resolved[WEB_SEARCH] == "web_search"
    assert res.resolved[WEB_FETCH] == "web_fetch"
    assert res.resolved["read"] == "view"
    assert res.resolved["write"] == "create"


def test_copilot_accepts_claude_name_aliases():
    # A profile that declares Claude names still resolves via the alias map.
    res = preflight("copilot-cli", ["WebSearch", "WebFetch", "Read", "Write"])
    assert res.status == "PASS"


def test_url_permission_does_not_create_web_tool():
    # /allow-all only widens URL access for tools that exist; it registers no
    # new tool, so the registered-tool set is unchanged and still BLOCKED.
    res = preflight("copilot-cli", COPILOT_REGRESSION)
    assert res.status == "BLOCKED"
    assert "URL permissions" in res.reason


# --- No silent fallbacks --------------------------------------------------

def test_blocked_reason_names_forbidden_fallbacks():
    res = preflight("copilot-cli", COPILOT_REGRESSION)
    for term in ("curl", "parent", "fabricated"):
        assert term in res.reason.lower()


# --- General adapter properties -------------------------------------------

def test_unknown_platform_is_blocked():
    res = preflight("bard-cli", CLAUDE_CODE_TOOLS)
    assert res.status == "BLOCKED"
    assert set(res.missing) == set(RESEARCH_CAPABILITIES)


def test_matching_is_case_insensitive():
    res = preflight("claude-code", ["websearch", "webfetch", "read", "write"])
    assert res.status == "PASS"


def test_every_platform_maps_every_capability():
    for plat in platforms():
        for cap in RESEARCH_CAPABILITIES:
            assert ADAPTERS[plat].get(cap), f"{plat} missing {cap}"


def test_claude_and_copilot_are_defined():
    assert {"claude-code", "copilot-cli"} <= set(platforms())


# --- CLI behaviour: reproducible exit codes for scripts/CI ----------------

def _run_cli(*args):
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return subprocess.run(
        [sys.executable, "-m", "contract.capabilities", *args],
        cwd=root, capture_output=True, text=True,
    )


def test_cli_pass_exit_zero():
    r = _run_cli("claude-code", *CLAUDE_CODE_TOOLS)
    assert r.returncode == 0
    assert "PASS" in r.stdout


def test_cli_blocked_exit_one():
    r = _run_cli("copilot-cli", *COPILOT_REGRESSION)
    assert r.returncode == 1
    assert "BLOCKED" in r.stdout


# --- End-to-end: a PASS run yields valid contract artifacts ---------------

def test_e2e_pass_produces_valid_artifacts(tmp_path):
    """PASS preflight -> write the three artifacts -> contract validator OK."""
    res = preflight("copilot-cli", COPILOT_WITH_WEB)
    assert may_produce_artifacts(res) is True

    out = tmp_path / "researchers" / "sub-01"
    out.mkdir(parents=True)
    (out / "findings.md").write_text(
        "# Findings\n\nExample finding backed by S001.\n", encoding="utf-8"
    )
    (out / "sources.jsonl").write_text(
        '{"source_id": "S001", "source_type": "official_docs", '
        '"title": "Example", "authority": "primary", '
        '"url": "https://example.org/doc", '
        '"retrieved_at": "2026-08-01T00:00:00Z"}\n',
        encoding="utf-8",
    )
    (out / "claims.jsonl").write_text(
        '{"claim_id": "C001", "statement": "Example is documented", '
        '"claim_kind": "fact", "confidence": "verified", '
        '"source_ids": ["S001"], "parent_claim_ids": [], '
        '"decision_relevant": false}\n',
        encoding="utf-8",
    )

    assert (out / "findings.md").exists()
    assert validate_run(str(out)) == []  # claims + sources pass the contract
