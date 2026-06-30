## Summary

- 
- 

## Challenge Surface

- [ ] This PR changes only allowed participant paths, or it is clearly marked as maintainer-only harness/governance work.
- [ ] No hidden cases, protected verifier file, generated `score.json`, local cache, or leaderboard artifact is committed.
- [ ] Public smoke timings are described as local/candidate telemetry only.
- [ ] Participant submissions did not edit `harness/**`, `cases/**`, `verifier/**`, `hidden_cases/**`, `challenge.json`, `score.json`, or `leaderboard/**`.

## Verification

- [ ] `scripts/run_smoke.sh`
- [ ] `python3 -m unittest discover -s tests`
- [ ] `python3 -m json.tool challenge.json`
- [ ] `python3 -m json.tool templates/submission.json`
- [ ] `python3 -m json.tool templates/leaderboard-entry.json`
- [ ] `python3 -m json.tool templates/promotion-packet.example.json`
- [ ] `python3 -m json.tool verifier/task-spec.json`
- [ ] `python3 scripts/validate_agent_notes.py --input templates/agent-notes.example.json`
- [ ] `python3 scripts/validate_replay_result.py --input templates/replay-result.example.json`
- [ ] `python3 scripts/validate_runner_manifest.py --input verifier/trusted-runner-manifest.example.json`
- [ ] `python3 scripts/validate_baseline_record.py --input verifier/baseline-record.example.json`
- [ ] `python3 scripts/validate_promotion_packet.py --input templates/promotion-packet.example.json`
- [ ] `git diff --check`

## Research Notes

List failed variants, numerical risks, hidden-shape concerns, timing variance, and integration-audit expectations.
