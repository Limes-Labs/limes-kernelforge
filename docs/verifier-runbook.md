# Trusted Verifier Runbook

This repository does not bundle hidden tensor cases or fixed-runner secrets.
The public contract in `verifier/replay-contract.json` describes what a trusted
runner must enforce before a KernelForge result can move beyond `candidate`.

## Replay Flow

1. Start from a clean checkout of the submitted commit.
2. Confirm the submission manifest passes:

   ```bash
   python3 scripts/check_submission.py --manifest submission.json --base origin/main
   ```

3. Disable network access for official scoring.
4. Mount trusted-only `hidden_cases/` with a private manifest and SHA-256
   hashes.
5. Run hidden correctness first using the contract tolerance matrix.
6. Time only correct submissions on the chosen fixed runner track.
7. Aggregate median per case and geomean across cases.
8. Run the invalid optimization audit and mini integration audit before
   promotion.
9. Emit the official result fields listed in `verifier/replay-contract.json`.

## Required Trusted Artifacts

- hidden case manifest and hashes;
- fixed runner hardware and software fingerprint;
- dependency lockfile or container digest;
- locked reference-baseline timings for the same runner track;
- warmup, repetition, timer, memory-cap, and aggregation logs;
- integration-audit result with the same code hash.

## Anti-Probing Notes

Hidden shapes must not be disclosed before candidate freeze. Public timings are
local telemetry only; official rankings require fixed-runner replay. Failed,
timed-out, or numerically unstable trusted runs should be recorded in result
cards when they influenced a promotion decision.
