---
name: learning
description: Structured learning sessions using The Math Academy Way. Manages session lifecycle, spaced retrieval, scaffolding, and proper file creation in learning-log/. USE WHEN user says 'learning session', 'study session', 'practice', 'review', 'spaced retrieval', 'learn', or references learning-log/ topics.
---

# Learning Session Manager (The Math Academy Way)

## When to Activate This Skill

- User wants to run a learning/study/practice session
- User asks to review topics or do spaced retrieval
- User references learning-log/ or LEARNING-CENTRE.md
- User says "let's practice", "quiz me", "review", "what's due"
- User wants to learn new material from clippings/

## Directory Structure

There are **two learning centres** — one for DSA/coding patterns, one for system design:

```
learning-log/
├── LEARNING-CENTRE.md              ← DSA / Coding Patterns (linked lists, hash maps, etc.)
├── README.md                       ← Methodology + file rules (shared)
├── how-to-learn.md                 ← Learning theory reference (shared)
├── {timestamp} - {Title}.md        ← DSA session logs
│
└── system-design/
    ├── LEARNING-CENTRE.md           ← System Design (URL shortener, rate limiter, etc.)
    └── {timestamp} - {Title}.md     ← System design session logs
```

When starting a session, check **both** learning centres for due reviews.

## Critical File Rules

> **EVERY session MUST produce a new timestamped file.**
> **NEVER append session data to a checkpoint or existing session file.**

### Before ANY session work

1. Read `learning-log/LEARNING-CENTRE.md` for DSA state
2. Read `learning-log/system-design/LEARNING-CENTRE.md` for system design state
3. Read `learning-log/README.md` for methodology reference
4. Get timestamp: `date -u +%Y-%m-%dT%H%M%S+0000`

### After session completion

1. **Create new file** in the correct directory:
   - DSA topics: `learning-log/{timestamp} - {Session Title}.md`
   - System design topics: `learning-log/system-design/{timestamp} - {Session Title}.md`
2. **Update** the corresponding `LEARNING-CENTRE.md` (session index, status, review dates)
3. **NEVER** edit checkpoint files or old session files to add new session data

## Session Protocol

### Step 1: Check What's Due

Read `learning-log/LEARNING-CENTRE.md` and check:
- Spaced Retrieval Schedule: topics with review date <= today
- In-progress topics (status 🟡) needing more practice
- New topics ready to start (dependencies met)

Present to user:
```
Due for review today: [list]
In progress (need practice): [list]
Ready to start: [list]
Suggested session plan: [review first, then new material]
```

### Step 2: Run the Session

**Standard Session (~45-60 min):**

| Phase | Time | Activity |
| --- | --- | --- |
| 1 | 10-15 min | **Spaced Retrieval** - Review due items from memory |
| 2 | 25-35 min | **New Material** - Scaffold, Practice, Automate |
| 3 | 5-10 min | **Discrimination Drill** - "Which pattern?" quick-fire |

**For each review topic:**
1. Ask user to recall from memory (no hints)
2. Grade: correct, partial, or failed
3. If failed: re-teach, re-scaffold, reset review interval

**For new material (The Cognitive Engine):**
1. **Direct Instruction** - Explain concept with worked example (minimal)
2. **Hyper-Scaffolding** - Fill-in-blank code, then partial code
3. **Deliberate Practice** - User writes from memory
4. **Automaticity** - Repeat until no hesitation

### Step 3: Log the Session

Get timestamp and create the session file using this template:

```markdown
# Learning Log: {Session Title}

**Date:** YYYY-MM-DD
**Duration:** ~XX minutes
**Type:** [Review / New Material / Interleaved / Diagnostic]
**Method:** Math Academy Way

---

## Session Structure

| Round | Task | Topic | Status |
| --- | --- | --- | --- |
| 1 | [Task name] | [Domain] | before -> after |

---

## [Topic 1]

**Status:** [before] -> [after]

### Scaffold Exercise
[Fill-in-blank or partial code]

### Full Implementation
[Code here]

### Errors Made
- [ ] Error 1
- [ ] Error 2

### Key Insight
[One-liner mnemonic or insight]

---

## Discrimination Drill

| Problem | Expected | Answered | Correct? |
| --- | --- | --- | --- |

---

## Next Actions
- [ ] Review X on [date]
- [ ] Practice Y
```

### Step 4: Update LEARNING-CENTRE.md

After creating the session file:
1. Add entry to Session Index with link to new file
2. Update topic statuses
3. Calculate next review dates (interval: 1, 2, 4, 7, 14 days)
4. Update Quick Stats counts
5. Update Recurring Errors Log if new errors found

## Status Codes

| Code | Meaning | Criteria |
| --- | --- | --- |
| ⬜ | Not started | Never practiced |
| 🟡 | In progress | Practiced but not fluent |
| ⚠️ | Shaky | Can do with hints, makes errors |
| ✅ | Solid | Can do from memory, no errors |
| 🔒 | Automated | Instant recall, used in harder problems |

## Spaced Retrieval Schedule

After reaching ✅ Solid, schedule reviews at increasing intervals:

| Review # | Interval | If Failed |
| --- | --- | --- |
| 1 | +1 day | Return to 🟡 |
| 2 | +2 days | - |
| 3 | +4 days | - |
| 4 | +7 days | - |
| 5 | +14 days | Move to 🔒 |

**Formula:** Next review = Last review + 2^n days, capped at 14

## Ingesting New Material

When user provides new clippings or source material:

1. Read all files in the source folder
2. Decompose into atomic knowledge points
3. Map dependencies (what must come before)
4. Identify core vs supplemental (80/20 rule)
5. Add topics to LEARNING-CENTRE.md
6. Start with diagnostic: find the knowledge frontier

## Key Principles (Math Academy Way)

1. **Map** dependencies before learning
2. **Diagnose** the knowledge frontier (where solid meets gaps)
3. **Scaffold** instruction to fit working memory capacity
4. **Automate** sub-skills through deliberate practice
5. **Schedule** spaced reviews to prevent forgetting
6. **Interleave** 3-4 different topics per session
7. **Discriminate** - drill "which pattern?" not just "apply pattern"

## Supplementary Resources

For full methodology: `read learning-log/how-to-learn.md`
For current progress: `read learning-log/LEARNING-CENTRE.md`
For file rules: `read learning-log/README.md`
