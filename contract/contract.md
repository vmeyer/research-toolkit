# Evidence Contract (research-toolkit v3)

Jeder Research-Schritt schreibt zwei maschinenlesbare Sidecars. Agents **lesen**
diese Datei; sie wird nicht in Briefs kopiert.

## claims.jsonl — eine atomare Aussage pro Zeile

```json
{
  "claim_id": "C012",
  "statement": "Atomare, überprüfbare Aussage",
  "claim_kind": "fact | inference | recommendation | gap",
  "confidence": "verified | inferred | reported | gap",
  "source_ids": ["S003", "S007"],
  "parent_claim_ids": [],
  "decision_relevant": true
}
```

Pflichtfelder: `claim_id`, `statement`, `claim_kind`, `confidence`, `source_ids`,
`parent_claim_ids`, `decision_relevant`. Optional: `valid_from`, `valid_to`, `tags`.

## sources.jsonl — eine Quelle pro Zeile

```json
{
  "source_id": "S003",
  "source_type": "official_docs | standard | academic | news | vendor_blog | code | runtime",
  "title": "…",
  "authority": "primary | secondary | tertiary",
  "url": "https://…",
  "repo": null, "commit": null, "path": null, "line_start": null, "line_end": null,
  "document_version": "Version/Datum",
  "retrieved_at": "2026-08-01T00:00:00Z",
  "content_hash": "sha256:…",
  "evidence_excerpt": "kurzer relevanter Beleg"
}
```

Pflichtfelder: `source_id`, `source_type`, `title`, `authority`, `retrieved_at`
und **entweder** `url` **oder** (`repo` **und** `path`). Empfohlen: `content_hash`,
`evidence_excerpt`, `document_version`.

## Die vier Regeln

1. **Aussageklasse Pflicht.** `fact` braucht ≥1 `source_ids`; `inference` braucht
   ≥1 `parent_claim_ids`; `recommendation` bewertet; `gap` benennt fehlende Evidenz.
2. **Gaps benennen, nicht erfinden.** Fehlende Evidenz → `gap`-Claim.
3. **Kein Citation Laundering.** `inference` ergänzt Originalquellen, ersetzt sie
   nicht; `parent_claim_ids` müssen auf `fact`-Claims mit echten Quellen zeigen.
4. **Dual-Source wo's zählt.** `decision_relevant: true` + `recommendation` →
   ≥2 unabhängige Quellen (verschiedener Publisher/Domain), sonst „vorläufig".

## ID-Räume

Leaf-Researcher vergeben lokale IDs (`C001…`, `S001…`) je Ordner. Der Verifier
normalisiert beim Merge in globale IDs und dedupliziert Quellen.

## Secrets/PII

Secrets, Tokens und personenbezogene Daten kommen nicht in `evidence_excerpt`.
Solche Quellen werden redigiert referenziert und mit `authority` + Zugriffsklasse
in `tags` gekennzeichnet.
