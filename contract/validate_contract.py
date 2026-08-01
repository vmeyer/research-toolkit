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
