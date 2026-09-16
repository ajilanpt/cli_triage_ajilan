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
The two ways a wrong answer costs money are not equal:

- **A real defect ships** (system leaned "flaky", it wasn't): ships to users, costs the
  company credibility and goodwill. Rough cost: **$5000**.
- **A flaky test is treated as a real defect** (false alarm): release is delayed/stopped
  for nothing, costs engineer time and a slipped deadline. Rough cost: **$500**.

Roughly a 10:1 asymmetry — shipping a real defect is far more expensive than a false alarm.
