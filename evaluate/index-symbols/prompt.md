# Skills evaluation

Run this evaluation in four phases.
Finish each phase and report before starting the next.

## 1. Build

Read the brief at `/Users/henrymckay/Library/Mobile Documents/com~apple~CloudDocs/Git/claude/evaluate/index-symbols/brief.md` and build exactly what it asks for, into the repository at `/Users/henrymckay/Library/Mobile Documents/com~apple~CloudDocs/Git/symbols/`.
The brief says whether that repository is new or one you are continuing.

Work only from your skills.
Invoke every one that applies and follow it.
Don't draw on anything in your saved memory: the point is to find out what the skills alone produce, so anything carried over from a previous run hides the gap being measured.

The brief fixes an interface and invites you to argue with it where your skills say a different shape would serve better.
Do that before you build rather than after, and build what I asked for unless I agree with you.

As you go, note explicitly anywhere a skill is silent, ambiguous or steers you wrong, rather than quietly working around it.
These notes are half the output, so record them when you hit them rather than reconstructing them at the end.

Read nothing else under `/Users/henrymckay/Library/Mobile Documents/com~apple~CloudDocs/Git/claude/evaluate/` — not this evaluation's `answers.md`, not another evaluation's anything — until you have told me the build is finished.

## 2. Grade

Open `/Users/henrymckay/Library/Mobile Documents/com~apple~CloudDocs/Git/claude/evaluate/index-symbols/answers.md` and grade the build against it.

Report every divergence.
For each, name the skill that should have caught it and quote the wording that failed to, or say plainly that no skill covers it.
Where the answers file is right and the build is wrong, say so rather than defending the build.

Work through the file section by section rather than reporting only what you already noticed, since the divergences you are blind to are the ones worth finding.
Two sections repay the most care: **what should not exist yet**, because structure built too early looks like diligence, and **wrong turns**, because each one is a failure a real run has made.

## 3. Improve

Fix the causes, not the transcript.
Two kinds of gap, fixed in two different places.

- A design the build should have reached but didn't is a **skill** gap.
  Change the skill so the next build reaches it unaided, stating the rule and the reason it exists rather than describing this build.
- A requirement the build could not have known is a **brief** gap.
  Add it to the brief as a requirement, never as design — the brief withholds the shape a good build reaches on purpose, and putting design there destroys the evaluation.
- Leave the answers file alone unless it is actually wrong.

Cover both the gaps you logged while building and the divergences the grading turned up.
They are different sets and both need closing.

The skills are at `/Users/henrymckay/Library/Mobile Documents/com~apple~CloudDocs/Git/claude/skills`.
Commit each change straight to `main` with a `docs(<skill-name>): ` scope, and push.

## 4. Realign

Bring the build into line with the fixes, so the repository is not left carrying divergences we have already agreed are wrong.
Check with me first on any change that trades correctness for speed, or that I chose deliberately while building.

Finish by reporting which gaps you closed, which you left, and why.
