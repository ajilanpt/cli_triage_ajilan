# Decision — split choice

## The deployment question
When this system runs in production, is it seeing tests from projects it has trained on, or
projects it has never seen?

**Projects it has never seen.** Nothing in `PROBLEM.md` ties this system to one specific
codebase — the on-call engineer and the 02:47 incident are described generically, and the
training data itself is 26,134 rows spread across 25 unrelated open-source projects (a
websocket library, an HTTP client, okhttp, ...), not many builds from one project. A single
trained model is meant to be dropped into a project's CI, including ones it has never trained
on — closer to a tool shipped to many teams than a model retrained per-project on accumulating
in-house history.

## The split
**Grouped by project** (`GroupKFold` on project identity), not a random row-wise split. A
random split would let rows from the same project land on both sides of a fold — the model
could learn project-specific quirks (naming conventions, a particular flaky test's exact
feature signature) and get credit for "generalizing" when it only memorized. A grouped split
where every project appears entirely on one side is the only split that measures what
production actually asks: perform on a project you were never trained on.

## Cost of getting this wrong
A random split would report an optimistic number that has nothing to do with deployment
performance — the system would look far better in development than it will behave for the
first real team that adopts it on a project outside the training set.
