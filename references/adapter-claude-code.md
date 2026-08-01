# Harness Adapter: Claude Code

**Capabilities:** `parallel: yes` · `dispatch: Agent tool` ·
`done-signal: harness completion notification` · `resume: file re-validate`.

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
