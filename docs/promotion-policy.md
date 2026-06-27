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
