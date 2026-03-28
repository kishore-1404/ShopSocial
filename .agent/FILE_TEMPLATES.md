# File Templates

> Used by the bootstrap check (Step 1) to create any missing `.agent/` files.
> These are minimal scaffolds — the agent fills them in as the project evolves.

## Template: REQUIREMENTS.md
```markdown
# REQUIREMENTS.md — Project Requirements

## Project Overview
**Project Name:** [fill in]
**Owner:** [fill in]
**Started:** [fill in]
**Version:** 0.1.0

### One-line summary
[What does this project do?]

### Problem it solves
[What pain does this solve, and for whom?]

### Target users
[Who are the primary users? Be specific.]

---

## Goals & Success Metrics
| Goal | Metric | Target |
|------|--------|--------|
| [e.g., Fast load] | [e.g., TTI] | [e.g., < 1.5s] |

---

## Core Features

### Feature 1: [Name]
**Status:** planned
**Priority:** High
**Acceptance Criteria:**
- [ ] [Specific, testable condition]

---

## Non-Functional Requirements
- Performance: [e.g., API p99 < 200ms]
- Security: [e.g., All data encrypted at rest]
- Accessibility: [e.g., WCAG 2.1 AA]

---

## Out of Scope
- [What will NOT be built]

## Change Log
| Date | Change | Author |
|------|--------|--------|
| [today] | Initial file created by ProjectAgent bootstrap | Agent |
```

## Template: STACK.md
```markdown
# STACK.md — Technology Stack

## Core Stack
| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Language | TypeScript | 5.x | strict mode |
| Runtime | Node.js | 20 LTS | |
| Framework | [fill in] | | |
| Styling | [fill in] | | |
| Database | [fill in] | | |
| Auth | [fill in] | | |
| Package manager | [fill in] | | |

## Frontend Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| [fill in] | | |

## Backend Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| [fill in] | | |

## External Services
| Service | Purpose | Notes |
|---------|---------|-------|
| [fill in] | | |

## Environment Variables
```bash
# Add all env vars here with comments
```

## Version History
| Date | Change |
|------|--------|
| [today] | Initial file created by ProjectAgent bootstrap |
```

## Template: INSTRUCTIONS.md
```markdown
# INSTRUCTIONS.md — Coding Rules & Conventions

## General Philosophy
- Clarity over cleverness
- Small changes, often
- No dead code — remove unused imports/variables immediately
- Fail loudly — errors must be explicit and informative
- One thing per function

## Naming Conventions
- Components: PascalCase
- Hooks: camelCase (useXxx)
- Utilities: camelCase
- Constants: SCREAMING_SNAKE_CASE
- Types/Interfaces: PascalCase
- API routes: kebab-case
- Test files: [name].test.[ext]

## TypeScript Rules
- strict: true — always
- No `any` — use `unknown` and narrow it
- No `as` assertions unless unavoidable — document why
- All function params and return types explicitly typed

## Error Handling
- All async functions must handle errors explicitly
- Never swallow errors silently
- User-facing errors must be human-readable
- Internal error details must never reach the client

## Testing Rules
- Every new function/component needs at least one test
- Test behaviour, not implementation
- Structure: Arrange → Act → Assert
- No test.only or test.skip merged to main

## Git Commit Format
Follow Conventional Commits:
- feat: new feature
- fix: bug fix
- refactor: no behaviour change
- test: tests only
- docs: documentation
- chore: tooling/config

## Pre-task Checklist
- [ ] No TypeScript errors, no `any`
- [ ] No unused imports
- [ ] No console.log / debug statements
- [ ] All new code has tests
- [ ] Error cases handled
- [ ] No hardcoded secrets
- [ ] CHANGELOG.md and CONTEXT.md updated

> Created by ProjectAgent bootstrap — fill in project-specific conventions.
```

## Template: CONTEXT.md
```markdown
# CONTEXT.md — Current Project State

> Updated after every session. The agent's working memory.

## Last Updated
**Date:** [today]
**Session summary:** Project initialised — .agent/ bootstrap complete.

---

## Current Sprint Focus
**Goal:** [fill in — what are we building right now?]
**Deadline:** [fill in or N/A]
**Priority order:**
1. [Top task]
2. [Second]
3. [Third]

---

## What Has Been Completed
- Project bootstrap — .agent/ folder created by ProjectAgent _(done: [today])_

---

## What Is In Progress
[None yet — fill in as work begins]

---

## What Is Blocked
[None]

---

## Recently Modified Files
[None yet]

---

## Known Issues & Bugs
[None yet]

---

## Environment State
- [ ] Development environment running
- [ ] Database connected and migrated
- [ ] Staging environment configured
- [ ] CI/CD pipeline set up
- [ ] Production deployed

---

## Important Notes for the Agent
- This project was just bootstrapped. Fill in REQUIREMENTS.md and STACK.md before starting feature work.
```

## Template: TASKS.md
```markdown
# TASKS.md — Task Tracker

> Updated at the start and end of every session.
> Add tasks here before writing any code.

## Current Sprint
| Task | Status | Priority | Assigned |
|------|--------|----------|----------|
| TASK-001 | backlog | P1 | Agent |

---

## Backlog

### TASK-001: Fill in project requirements and stack
**Status:** backlog
**Priority:** P1
**Effort:** S
**Type:** docs
**Assigned:** Developer + Agent
**Created:** [today]

**Description:**
Update REQUIREMENTS.md with actual project details and STACK.md with the real tech stack before feature work begins.

**Acceptance Criteria:**
- [ ] REQUIREMENTS.md has project name, summary, target users, and at least one feature defined
- [ ] STACK.md has all core dependencies listed with versions

---

## Done
| Task | Title | Completed | Notes |
|------|-------|-----------|-------|
| TASK-000 | .agent/ bootstrap | [today] | Created by ProjectAgent on first run |

---

## Task Number Counter
Last task number used: **001**
```

## Template: CHANGELOG.md
```markdown
# CHANGELOG.md — Agent Change Log

> Every meaningful code change is logged here. Newest entries at the top.

---

### [TODAY] — Project bootstrap

**Task:** .agent/ folder initialisation
**Triggered by:** First ProjectAgent session — bootstrap check found missing files

**Changes:**
- `.agent/REQUIREMENTS.md` — created from template
- `.agent/STACK.md` — created from template
- `.agent/INSTRUCTIONS.md` — created from template
- `.agent/CONTEXT.md` — created from template
- `.agent/TASKS.md` — created from template
- `.agent/CHANGELOG.md` — created from template
- `.agent/DECISIONS.md` — created from template
- `.agent/IMPROVEMENTS.md` — created from template
- `.agent/SECURITY.md` — created from template

**Tests:** N/A — setup only
**Notes:** All files are templates. Developer should fill in project-specific details before feature work.
**Breaking changes:** No
```

## Template: DECISIONS.md
```markdown
# DECISIONS.md — Architecture Decision Records

> Every significant technical decision recorded here.
> Never delete entries — mark as `superseded` and add a new one.

---

## ADR Format
### ADR-NNN: [Title]
**Date:** [date]
**Status:** proposed | accepted | superseded | deprecated
**Decided by:** Agent | Developer | Team

**Context:** [What prompted this decision?]
**Options considered:**
1. [Option A] — [trade-offs]
2. [Option B] — [trade-offs]
**Decision:** [What was chosen and why]
**Consequences:**
- Good: [positive outcomes]
- Bad: [accepted trade-offs]

---

### ADR-001: Use .agent/ folder for persistent agent memory

**Date:** [today]
**Status:** accepted
**Decided by:** Developer

**Context:**
AI agents lose context between sessions. Without a persistent knowledge base, each session starts from scratch — leading to inconsistent conventions, repeated decisions, and lost context about what was built and why.

**Options considered:**
1. Rely on git history and comments — cheap but not agent-readable or structured
2. Use a single large context file — hard to maintain, hard to read selectively
3. Use a `.agent/` folder with purpose-specific files — structured, readable, maintainable

**Decision:**
Option 3 — `.agent/` folder with 9 purpose-specific files, each with a clear scope.

**Consequences:**
- Good: Agent has structured, predictable knowledge. Each file has a single purpose.
- Bad: Files must be kept up to date — stale files are worse than no files.
- Neutral: Adds ~10 files to the repo root. Should be committed alongside code.
```

## Template: IMPROVEMENTS.md
```markdown
# IMPROVEMENTS.md — Improvement Backlog

> The agent's honest assessment of what could be better.
> Not a task list — an observation log. Developer decides what becomes a task.

---

## Priority Levels
- **P0:** Fix now — causing bugs, security risks, or blocking development
- **P1:** Fix soon — significant debt that will slow us down
- **P2:** Fix eventually — real problems, not urgent
- **P3:** Nice to have — polish, optimisation, quality of life

## Effort Estimates
- **S:** < 2 hours  |  **M:** half a day  |  **L:** multiple days

---

## Active Items

### IMP-001: Fill in project-specific details across .agent/ files

**Priority:** P1
**Effort:** S
**Found:** [today]
**Location:** All `.agent/` files

**Observation:**
All `.agent/` files were created from templates. They contain placeholders that need to be filled in with real project information before the agent can operate at full effectiveness.

**Why it matters:**
The agent's knowledge base is only as good as the information in it. Placeholder files lead to generic, unconstrained agent behaviour.

**Suggested approach:**
Developer fills in REQUIREMENTS.md and STACK.md first (20 min). Agent can assist with the rest during the first real session.

**Promoted to task?** Yes — TASK-001

---

## Closed / Won't Fix
| ID | Title | Reason |
|----|-------|--------|
| — | — | — |
```

## Template: SECURITY.md
```markdown
# SECURITY.md — Security Rules

> Non-negotiable. These override task requirements.
> Check this file before touching auth, user data, env vars, file system, or external APIs.
> If a task conflicts with a rule here — STOP and flag it to the developer.

---

## 1. Credentials & Secrets
**NEVER:**
- Hardcode any API key, token, password, secret, or connection string
- Log or print any credential — even in error messages
- Store secrets in localStorage, sessionStorage, or non-httpOnly cookies
- Commit .env or any file containing real secrets

**ALWAYS:**
- Read secrets from environment variables only
- Validate required env vars exist at startup (fail fast)
- Add new env vars to .env.example with a description comment

---

## 2. Authentication & Authorisation
**NEVER:**
- Trust client-supplied user IDs for data access decisions
- Expose admin endpoints without role checks
- Use GET for state-changing operations
- Skip CSRF protection on forms

**ALWAYS:**
- Validate the session server-side on every protected request
- Check permissions at the resource level, not just the route level
- Log failed auth attempts (not the credentials — just the event)

---

## 3. Input Validation
**NEVER:**
- Trust any data from the client without server-side validation
- Use dangerouslySetInnerHTML unless content is sanitised
- Pass user input directly into SQL queries or shell commands

**ALWAYS:**
- Validate all incoming data using a schema (Zod, Joi, etc.) at the API boundary
- Sanitise user-generated content before storing or rendering

---

## 4. Data Privacy
**NEVER:**
- Log PII — names, emails, phone numbers, IPs
- Return full user objects when a subset is enough
- Store passwords unencrypted

**ALWAYS:**
- Hash passwords with bcrypt (cost ≥ 12) or Argon2
- Apply principle of least privilege to all API responses

---

## 5. Protected Files — Do Not Modify Without Developer Approval
```
.env
.env.local
.env.production
[any migration files applied to production]
[auth configuration files]
```

---

## 6. Security Incident Response
If you detect or create a security vulnerability:
1. Stop immediately
2. Add it to IMPROVEMENTS.md as P0
3. Alert the developer with: what it is, where it is, how it could be exploited, recommended fix
4. Do not attempt to fix it silently — security fixes require developer review

---

## 7. Security Checklist (Before Completing Any Task)
- [ ] No secrets in code
- [ ] All inputs validated server-side
- [ ] Auth checks on new routes
- [ ] No PII in logs
- [ ] CORS and rate limiting considered for new public endpoints
- [ ] New dependencies checked for CVEs
```

---
