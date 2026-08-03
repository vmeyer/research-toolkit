# Harness Adapter: Claude Code

**Platform id:** `claude-code`

**Capabilities:** `parallel: yes` · `dispatch: Agent tool` ·
`done-signal: harness completion notification` · `resume: file re-validate`.

## Tool capability mapping

The canonical capabilities (see [`capability-model.md`](capability-model.md))
map 1:1 to native Claude Code tools; the source of truth is
`contract/capabilities.py`:

| Canonical capability | Claude Code tool |
|----------------------|------------------|
| `web_search`         | `WebSearch`      |
| `web_fetch`          | `WebFetch`       |
| `read`               | `Read`           |
| `write`              | `Write`          |

`researcher-1` and `verifier-1` therefore declare `WebSearch, WebFetch, Read,
Write` in their frontmatter under this harness. URL permission
(`--allow-all-urls`) only widens which URLs `WebFetch` may reach — it does not
create tools.

## Capability preflight (mandatory, before research)

Before dispatching researchers, run the shared preflight from
[`capability-model.md`](capability-model.md):

```bash
python -m contract.capabilities claude-code WebSearch WebFetch Read Write
# -> PASS; exit 0
```

Then live-probe `web_search`, `web_fetch`, `read`, `write` and record
`preflight/capability-probe.json`. On any BLOCKED capability, set
`state.status: blocked` and stop **before** writing any research artifact — no
`curl`/parent-agent/other-agent/fabricated-source fallback.

## Worker dispatchen
- Alle parallelen Leaf-Researcher **in einer einzigen Message** starten (mehrere
  `Agent`-Aufrufe im selben Turn) → echte Parallelität.
- Jeder Worker bekommt: seinen Sub-Brief, den Pfad zu `contract/contract.md`
  (lesen, nicht kopieren), seinen exklusiven Output-Ordner `researchers/sub-NN/`,
  die absoluten Ausgabepfade (`findings.md`, `claims.jsonl`, `sources.jsonl`).
- Worker persistieren selbst; der Orchestrator rekonstruiert keine fehlende
  Ausgabe aus der Agent-Antwort.

## "done" erkennen
- Nie Stdout parsen. Der Harness meldet Worker-Abschluss.
- Nach Abschluss: Existenz + Parsebarkeit der Sidecars prüfen
  (`python -m contract.validate_contract researchers/sub-NN`).

## Sequenzielle Degradation
- Ist Parallel-Dispatch nicht verfügbar, Worker nacheinander starten. Gleiche
  Dateien, gleiches Gate — nur langsamer.

## State/Resume
- `state.yaml` ist die Wahrheit. Bei Wiedereintritt: lesen, referenzierte Dateien
  re-validieren, beim ersten nicht-`done`-Schritt fortsetzen.
