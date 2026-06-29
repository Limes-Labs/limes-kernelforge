# Agent Notes Policy

Agent notes are hints for future investigation, not proof.

Every agent-run submission should preserve:

- primitive targeted;
- public and private commands used;
- timing variance and failed variants;
- numerical error observations;
- lineage from previous submissions;
- hidden-shape assumptions that must be tested later.

Notes should help future agents avoid repeated dead ends, but every claim still
needs trusted replay and integration audit.

Use `templates/agent-notes.example.json` as the machine-checkable shape for
agent-run notes. Validate completed notes with:

```bash
python3 scripts/validate_agent_notes.py --input templates/agent-notes.example.json
```

The validator requires exactly one selected attempt, preserves rejected or mixed
attempts when multiple trials were run, and requires timing variance notes,
hidden-shape assumptions, numerical risks, and negative or mixed findings.
