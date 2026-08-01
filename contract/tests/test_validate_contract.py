import pytest
from contract.validate_contract import validate_claims, validate_sources

def _claim(**over):
    base = {
        "claim_id": "C001", "statement": "x", "claim_kind": "fact",
        "confidence": "verified", "source_ids": ["S001"],
        "parent_claim_ids": [], "decision_relevant": False,
    }
    base.update(over)
    return base

def _source(**over):
    base = {
        "source_id": "S001", "source_type": "official_docs", "title": "t",
        "authority": "primary", "url": "https://a.example/doc",
        "retrieved_at": "2026-08-01T00:00:00Z",
    }
    base.update(over)
    return base

def test_valid_claim_passes():
    assert validate_claims([_claim()]) == []

def test_duplicate_claim_id_fails():
    errs = validate_claims([_claim(), _claim()])
    assert any("duplicate" in e.lower() for e in errs)

def test_invalid_claim_kind_fails():
    errs = validate_claims([_claim(claim_kind="opinion")])
    assert any("claim_kind" in e for e in errs)

def test_fact_without_source_fails():
    errs = validate_claims([_claim(claim_kind="fact", source_ids=[])])
    assert any("fact" in e.lower() and "source" in e.lower() for e in errs)

def test_inference_without_parent_fails():
    errs = validate_claims([_claim(claim_kind="inference", parent_claim_ids=[])])
    assert any("inference" in e.lower() and "parent" in e.lower() for e in errs)

def test_gap_without_source_passes():
    assert validate_claims([_claim(claim_kind="gap", source_ids=[])]) == []

def test_valid_source_passes():
    assert validate_sources([_source()]) == []

def test_source_missing_anchor_fails():
    errs = validate_sources([_source(url=None)])
    assert any("anchor" in e.lower() or "url" in e.lower() for e in errs)

def test_source_code_anchor_passes():
    s = _source(url=None, repo="r", path="p/f.py", line_start=1, line_end=9)
    assert validate_sources([s]) == []
