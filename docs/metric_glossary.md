***
# HEIMDALL Metric Glossary
***
## Cycle Time

**Definition:**

Time between first entry into in-progress state and final completion.

**Why it matters:**

Measures delivery speed.

**How computed:**

Derived from transition event timestamps.

**Limitations:**

Undefined if issue never enters in-progress.


---

## Throughput

**Definition:**

Number of issues completed per day.

**Why it matters:**

Measures delivery capacity.

**Computed from:**

fct_issue_lifecycle.done_at


---

## Work in Progress (WIP)

**Definition:**

Number of issues actively being worked on at a point in time.

**Why it matters:**

High WIP increases delivery time.


---

## Blocked Time

**Definition:**

Total time an issue was blocked during its active lifecycle.

**Why it matters:**

Identifies delivery friction.


---

## Reopen Count

**Definition:**

Number of times an issue returned to active work after completion.

**Why it matters:**

Measures quality and rework.
