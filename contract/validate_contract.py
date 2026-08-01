"""Contract validator for research-toolkit v3 evidence sidecars."""
from __future__ import annotations
import json

CLAIM_KINDS = {"fact", "inference", "recommendation", "gap"}
CONFIDENCE_VALUES = {"verified", "inferred", "reported", "gap"}
SOURCE_TYPES = {"official_docs", "standard", "academic", "news",
                "vendor_blog", "code", "runtime"}
AUTHORITY_VALUES = {"primary", "secondary", "tertiary"}

_CLAIM_REQUIRED = ["claim_id", "statement", "claim_kind", "confidence",
                   "source_ids", "parent_claim_ids", "decision_relevant"]
_SOURCE_REQUIRED = ["source_id", "source_type", "title", "authority",
                    "retrieved_at"]


def load_jsonl(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def validate_claims(claims: list[dict]) -> list[str]:
    errs: list[str] = []
    seen = set()
    for c in claims:
        cid = c.get("claim_id", "<missing>")
        for f in _CLAIM_REQUIRED:
            if f not in c:
                errs.append(f"claim {cid}: missing required field '{f}'")
        if cid in seen:
            errs.append(f"claim {cid}: duplicate claim_id")
        seen.add(cid)
        kind = c.get("claim_kind")
        if kind not in CLAIM_KINDS:
            errs.append(f"claim {cid}: invalid claim_kind '{kind}'")
        if c.get("confidence") not in CONFIDENCE_VALUES:
            errs.append(f"claim {cid}: invalid confidence '{c.get('confidence')}'")
        if kind == "fact" and not c.get("source_ids"):
            errs.append(f"claim {cid}: fact requires >=1 source_ids")
        if kind == "inference" and not c.get("parent_claim_ids"):
            errs.append(f"claim {cid}: inference requires >=1 parent_claim_ids")
    return errs


def validate_sources(sources: list[dict]) -> list[str]:
    errs: list[str] = []
    seen = set()
    for s in sources:
        sid = s.get("source_id", "<missing>")
        for f in _SOURCE_REQUIRED:
            if f not in s:
                errs.append(f"source {sid}: missing required field '{f}'")
        if sid in seen:
            errs.append(f"source {sid}: duplicate source_id")
        seen.add(sid)
        if s.get("source_type") not in SOURCE_TYPES:
            errs.append(f"source {sid}: invalid source_type '{s.get('source_type')}'")
        if s.get("authority") not in AUTHORITY_VALUES:
            errs.append(f"source {sid}: invalid authority '{s.get('authority')}'")
        has_url = bool(s.get("url"))
        has_code = bool(s.get("repo")) and bool(s.get("path"))
        if not (has_url or has_code):
            errs.append(f"source {sid}: missing anchor (need url OR repo+path)")
    return errs


import os
from urllib.parse import urlparse


def _domain(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url).netloc.lower()
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def validate_cross_refs(claims: list[dict], sources: list[dict]) -> list[str]:
    errs: list[str] = []
    src_ids = {s.get("source_id") for s in sources}
    claim_ids = {c.get("claim_id") for c in claims}
    for c in claims:
        cid = c.get("claim_id")
        for sref in c.get("source_ids", []):
            if sref not in src_ids:
                errs.append(f"claim {cid}: unresolvable source_id '{sref}'")
        for pref in c.get("parent_claim_ids", []):
            if pref not in claim_ids:
                errs.append(f"claim {cid}: unresolvable parent_claim_id '{pref}'")
    return errs


def validate_decision_rules(claims: list[dict], sources: list[dict]) -> list[str]:
    errs: list[str] = []
    by_id = {s.get("source_id"): s for s in sources}
    for c in claims:
        if not (c.get("decision_relevant") and c.get("claim_kind") == "recommendation"):
            continue
        refs = c.get("source_ids", [])
        keys = set()
        for sref in refs:
            s = by_id.get(sref, {})
            keys.add(_domain(s.get("url")) or s.get("publisher") or s.get("repo") or sref)
        if len(keys) < 2:
            errs.append(
                f"claim {c.get('claim_id')}: decision-relevant recommendation "
                f"needs >=2 independent sources (distinct publisher/domain)"
            )
    return errs


def validate_run(run_dir: str) -> list[str]:
    errs: list[str] = []
    cpath = os.path.join(run_dir, "claims.jsonl")
    spath = os.path.join(run_dir, "sources.jsonl")
    for p in (cpath, spath):
        if not os.path.exists(p):
            errs.append(f"missing required file: {p}")
    if errs:
        return errs
    claims = load_jsonl(cpath)
    sources = load_jsonl(spath)
    errs += validate_claims(claims)
    errs += validate_sources(sources)
    errs += validate_cross_refs(claims, sources)
    errs += validate_decision_rules(claims, sources)
    return errs


if __name__ == "__main__":
    import sys
    problems = validate_run(sys.argv[1])
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print("OK")
