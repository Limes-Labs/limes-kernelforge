# Promotion Policy

KernelForge uses explicit status labels:

```text
local -> candidate -> verified -> promoted -> replicated -> scaled
```

- `local`: contributor-run public smoke telemetry.
- `candidate`: submitted diff worth replay.
- `verified`: trusted runner reproduced correctness and timing.
- `promoted`: accepted into the public frontier.
- `replicated`: repeated fixed-runner runs agree within policy.
- `scaled`: larger shape or integration audit preserves the improvement.

Public smoke timings never receive official rank by themselves.

Before any fixed-runner replay is scheduled, the candidate must have a
validated replay request. The request binds the candidate packet, runner track,
replay quota, freeze state, and anti-probing declarations. A replay request can
ask only for `verified`; later status changes require replay and promotion
packets.

Promotion requests must include a validated promotion packet. The packet binds
the submission manifest, agent notes, trusted-runner manifest, locked reference
baseline, replay result, result card, leaderboard entry, fixed runner track,
correctness evidence, tolerance evidence, and audit gates. A fast public smoke
number or a replay result alone is not enough for `promoted` or later status.

Schema-only examples may validate, but they must keep `promotion_ready` false
and must state that they are not official promotion packets.
