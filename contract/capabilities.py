"""Platform capability adapter + preflight gate for research-toolkit.

The research and verify agents need four *canonical, platform-neutral*
capabilities: web search, web fetch, file read, and file write. Different
harnesses expose those capabilities under different tool names (Claude Code:
``WebSearch``/``WebFetch``/``Read``/``Write``; Copilot CLI: ``web``/``view``/
``edit`` …). A platform adapter maps each canonical capability to the tool
names that satisfy it on that platform.

The **preflight gate** resolves the tools that are *actually registered* in
the harness against the required capabilities BEFORE any research artifact is
produced. A missing capability yields ``BLOCKED`` — never a silent fallback via
curl, the parent agent, another research agent, or fabricated sources.

Important nuance encoded here: URL permissions (``--allow-all-urls`` /
``/allow-all``) only unlock tools that already exist. They cannot register a
capability the harness never provided, so they can never turn a ``BLOCKED``
web-tool preflight into a ``PASS``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

# --- Canonical, platform-neutral capabilities -----------------------------
WEB_SEARCH = "web_search"
WEB_FETCH = "web_fetch"
READ = "read"
WRITE = "write"

# What researcher-1 and verifier-1 both require to do real research.
RESEARCH_CAPABILITIES: tuple[str, ...] = (WEB_SEARCH, WEB_FETCH, READ, WRITE)

# platform -> capability -> ordered list of acceptable tool names (aliases).
# The FIRST alias is the platform's canonical/preferred name; the rest are
# accepted equivalents so an operator-registered MCP tool can satisfy the gate.
ADAPTERS: dict[str, dict[str, list[str]]] = {
    "claude-code": {
        WEB_SEARCH: ["WebSearch"],
        WEB_FETCH: ["WebFetch"],
        READ: ["Read"],
        WRITE: ["Write"],
    },
    "copilot-cli": {
        # Copilot CLI ships native web tools; the canonical names are
        # web_search / web_fetch (verified against the bundled SDK alias table:
        # web_fetch->WebFetch, web_search->WebSearch, view->Read, create->Write,
        # edit->Edit). The Claude names are accepted aliases; `web` is only an
        # optional name an MCP server might use. See adapter-copilot-cli.md.
        WEB_SEARCH: ["web_search", "WebSearch", "web"],
        WEB_FETCH: ["web_fetch", "WebFetch", "fetch", "web"],
        READ: ["view", "Read", "read"],
        WRITE: ["create", "edit", "Write", "Edit", "write"],
    },
}


def platforms() -> list[str]:
    """Names of the platforms with a defined adapter."""
    return sorted(ADAPTERS)


@dataclass
class PreflightResult:
    """Outcome of a capability preflight for one platform."""

    platform: str
    status: str  # "PASS" | "BLOCKED"
    resolved: dict[str, str] = field(default_factory=dict)  # capability -> tool
    missing: list[str] = field(default_factory=list)  # unsatisfied capabilities
    reason: str = ""

    @property
    def blocked(self) -> bool:
        return self.status == "BLOCKED"

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


def _match(aliases: Iterable[str], available_lower: set[str]) -> str | None:
    """Return the first alias present in the registered tool set, else None."""
    for alias in aliases:
        if alias.lower() in available_lower:
            return alias
    return None


def preflight(
    platform: str,
    available_tools: Iterable[str],
    required: Iterable[str] = RESEARCH_CAPABILITIES,
) -> PreflightResult:
    """Resolve registered tools against required capabilities for a platform.

    ``available_tools`` is the set of tool names the harness has actually
    registered for the agent (case-insensitive). Any required capability with
    no matching tool makes the result ``BLOCKED``.
    """
    required = list(required)
    if platform not in ADAPTERS:
        return PreflightResult(
            platform=platform,
            status="BLOCKED",
            missing=required,
            reason=(
                f"unknown platform '{platform}'; known platforms: "
                + ", ".join(platforms())
            ),
        )

    mapping = ADAPTERS[platform]
    available_lower = {t.lower() for t in available_tools}
    resolved: dict[str, str] = {}
    missing: list[str] = []
    for cap in required:
        hit = _match(mapping.get(cap, []), available_lower)
        if hit is None:
            missing.append(cap)
        else:
            resolved[cap] = hit

    if missing:
        reason = (
            f"{platform}: BLOCKED — no registered tool for "
            + ", ".join(missing)
            + ". Both harnesses provide web tools natively (Claude Code: "
            "WebSearch/WebFetch; Copilot CLI: web_search/web_fetch), so this "
            "usually means the agent profile declared tool names the harness did "
            "not recognize — declare the harness's own names. URL permissions "
            "(--allow-all-urls / /allow-all) only unlock tools that already "
            "exist; they cannot register a missing tool. Fallbacks via curl, the "
            "parent agent, another research agent, or fabricated sources are "
            "forbidden."
        )
        return PreflightResult(platform, "BLOCKED", resolved, missing, reason)

    return PreflightResult(
        platform=platform,
        status="PASS",
        resolved=resolved,
        reason=f"{platform}: PASS — all required capabilities are registered.",
    )


def may_produce_artifacts(result: PreflightResult) -> bool:
    """Gate helper: research artifacts may only be written after a PASS.

    Use this to guard artifact creation so a BLOCKED run leaves the output
    folder empty (no findings.md / claims.jsonl / sources.jsonl).
    """
    return result.passed


def _cli(argv: list[str]) -> int:
    if not argv:
        print("usage: python -m contract.capabilities <platform> [registered_tool ...]")
        print("platforms: " + ", ".join(platforms()))
        return 2
    platform, tools = argv[0], argv[1:]
    res = preflight(platform, tools)
    print(f"platform: {res.platform}")
    print(f"status:   {res.status}")
    for cap in RESEARCH_CAPABILITIES:
        print(f"  {cap:11} -> {res.resolved.get(cap, '<MISSING>')}")
    print(res.reason)
    return 1 if res.blocked else 0


if __name__ == "__main__":
    import sys

    sys.exit(_cli(sys.argv[1:]))
