# Decision — output space

## Starting point
Three outputs, one per cause: real defect / flaky / infra.

## The case that forced a fourth
A test with no history — brand new, one single failure, nothing to compare against. The
system has no honest basis to pick one of the three; a confident-looking guess here is
worse than no answer, because the engineer may trust a probability the system had almost no
evidence for.

## The fourth output: ABSTAIN
Emitted when the evidence is too thin to support any of the three causes.

**What happens downstream when it fires:** the engineer gets no recommendation at all and
manually analyzes the failure and decides — this is distinct from a low-confidence "flaky"
or "defect" verdict, which still carries a recommendation. Abstain must trigger a different
action (manual investigation) than any of the three causes, or it is not really wired to
anything.
