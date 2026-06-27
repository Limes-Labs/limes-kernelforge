## Summary

- 
- 

## Challenge Surface

- [ ] This PR changes only allowed participant paths, or it is clearly marked as maintainer-only harness/governance work.
- [ ] No hidden cases, generated `score.json`, local cache, or leaderboard artifact is committed.
- [ ] Public smoke timings are described as local/candidate telemetry only.

## Verification

- [ ] `scripts/run_smoke.sh`
- [ ] `python3 -m unittest discover -s tests`
- [ ] `python3 -m json.tool challenge.json`
- [ ] `python3 -m json.tool templates/submission.json`
- [ ] `python3 -m json.tool templates/leaderboard-entry.json`
- [ ] `git diff --check`

## Research Notes

List failed variants, numerical risks, hidden-shape concerns, timing variance, and integration-audit expectations.
