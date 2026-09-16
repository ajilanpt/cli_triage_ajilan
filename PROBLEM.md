# Problem

## 1. The decision
At 02:47, a build on the release branch goes red. **The on-call release engineer** must
decide what to do with the release, **before 09:00** when it is due to ship.

## 2. The actions
The engineer has exactly three real moves:

- **Release** — ship anyway.
- **Stop the release** — hold it, treat the failure as a real defect.
- **Rerun the test** — get one more piece of evidence before deciding.

## 3. The prediction
The system estimates a **probability distribution over the real state of the build**:
real defect / flaky test / infra hiccup.

This is not the same as the decision. A probability like "70% flaky" does not say what to
do with that 70% — someone (or a policy) still has to decide whether that is confident
enough to release, or whether it is safer to rerun first. The prediction is an estimate of
reality; the decision is the action a human takes under a deadline.

## 4. The cost
One row per (true cause, system output) pair that leads to a wrong action:

| True cause | System says | Cost | Why |
|---|---|---|---|
| real defect | flaky | $5000 | ships to users |
| real defect | infra | $4000 | rerun may let an intermittent defect slip through |
| real defect | abstain | $200 | manual investigation, resolved before shipping |
| flaky | real defect | $500 | release delayed for nothing |
| flaky | infra | $400 | rerun resolves nothing but causes no harm |
| flaky | abstain | $200 | manual investigation of a flaky test |
| infra | real defect | $500 | release delayed for a machine hiccup |
| infra | flaky | $300 | ships fine now, but the infra fault stays unflagged and can recur |
| infra | abstain | $200 | manual investigation of a machine hiccup |

**Not symmetric.** Anything that risks a real defect shipping ($5000, $4000) costs 10-25x
more than a false alarm ($500) or a mix-up between the two benign causes ($300-400).
Roughly a 10:1 asymmetry between the worst case and the routine false alarm.

**ABSTAIN is cheap, not free.** Flat $200 regardless of the true cause — the cost of the
engineer's manual investigation. It exists because it is cheaper than a wrong guess in any
row above it, not because it costs nothing.

## 5. The objective
Minimize the expected cost from the table above (cost-weighted risk), not accuracy —
because accuracy weighs every mistake the same, and this table shows they aren't.
