# [Project Name] - Development Constitution

## 1. Roles & Introductions

- **Manager:** **Ahmad**. The owner, final decision-maker, and release approver for this project.
- **Developer AI:** **Qwen**. Responsible for implementation, bug fixing, refactoring, and writing tests.
- **Consultant AI:** **Gem**. Responsible for architecture guidance, strategic planning, and high-level technical review.
- **Reviewer AI:** **Cod**. Responsible for code review, regression detection, verification discipline, and implementation support when needed.

---

## 2. How to Use This Constitution

- **Sequential Execution:** Work must proceed phase-by-phase. Do not skip ahead.
- **Task-Based Execution:** Each phase must be split into smaller tasks before implementation begins.
- **No Implicit Completion:** A phase or task is not complete because code was written. It is complete only after verification passes.
- **Manager Approval Rule:** A phase may be merged to `master` only after Ahmad explicitly approves it.
- **Branch-Only Work:** All implementation, fixes, and experiments must happen in branches, never directly on `master`.

---

## 3. Core Methodological Mandates

- **Zero-Error Policy:** Never claim completion without empirical verification.
- **Testing Mandate:** Every feature must include corresponding automated tests.
- **Verification Mandate:** Run the relevant test suite before every commit and before every merge proposal.
- **Small, Controlled Scope:** Each task should target one clear functional outcome.
- **Services-First Business Logic:** Keep business logic in `services.py` or equivalent service modules, not in `views.py`.
- **Views Architecture:**
  - **CBVs:** Use for structural pages, dashboards, CRUD flows, and reusable view behavior.
  - **FBVs:** Use only for small HTMX endpoints, polling handlers, or lightweight actions.
- **Frontend Separation:**
  - No inline CSS unless there is a strict technical reason.
  - Keep CSS in `static/css/`.
  - Keep JavaScript in `static/js/`.
  - Keep reusable template fragments in `templates/components/`.

---

## 4. Git & Workflow Standards

- **No Direct Master Commits:** `master` must remain stable and production-safe.
- **Remote-First Workflow:** Every branch must be pushed to `origin` immediately after creation or after the first meaningful commit.
- **Branch Naming Convention:**
  - `phase-<name>` for active feature phases
  - `fix-<description>` for bugs already present in `master`
  - `chore-<description>` for non-feature maintenance when explicitly approved
- **Commit Standard:** Every commit must contain:
  - A concise title
  - A detailed body explaining why the change was made
- **Branch Iteration Rule:** During a phase, it is acceptable to commit and push multiple times while fixing issues. Keep all incomplete work off `master`.
- **Merge Rule:** A branch is merged only when:
  - The relevant tests pass
  - Manual verification is done when applicable
  - Ahmad approves the milestone
- **Cleanup Rule:** Delete local and remote branches only after successful merge and confirmation that no follow-up changes remain.

---

## 5. Phase Methodology

Each project must define its roadmap as a set of numbered phases.

Each phase must contain:
- **Phase Goal:** The business or technical objective.
- **Concepts:** The main technical ideas or patterns involved.
- **Tasks:** Small execution units inside the phase.
- **Deliverables:** The concrete outputs expected at phase completion.
- **Verification:** The commands or manual checks required to prove the phase works.

### Phase Execution Rule

- Do not implement an entire phase as one large block of work.
- First split the phase into tasks.
- Execute tasks one by one.
- Review each task before treating the phase as complete.

### Recommended Task Size

A task should be:
- Small enough for one focused implementation cycle
- Large enough to create meaningful progress
- Clear enough that another agent can execute it without guessing

---

## 6. Task Methodology

Tasks are the required execution layer inside each phase.

Each task must contain:
- **Task ID:** Example `1.1`, `1.2`, `2.3`
- **Task Name:** Short and specific
- **Goal:** What this task is meant to achieve
- **Scope:** What is included and what is excluded
- **Expected Files:** Files or directories likely to be touched
- **Implementation Notes:** Important constraints or architectural rules
- **Tests Required:** Unit, integration, UI, or smoke tests expected
- **Verification:** Exact command or manual check
- **Done Criteria:** What must be true before the task is considered complete

### Task Completion Rule

A task is complete only when:
- The implementation is finished
- Relevant tests are written
- Relevant tests pass
- Manual verification is done if needed
- The reviewer finds no blocking issues

### Task Handoff Rule

When one AI tool hands off work to another, the handoff must state:
- Current phase
- Current task ID and name
- What was completed
- What remains
- What verification already passed
- Any known risks, blockers, or assumptions

---

## 7. Phase Template

Use the following structure for every project-specific phase:

```md
## Phase [Number]: [Phase Name]

**Goal:** [Describe the phase objective]

**Concepts:** [Key technical ideas]

### Tasks

#### Task [Number].[Number]: [Task Name]
- **Goal:** [Describe the task objective]
- **Scope:** [What is included and excluded]
- **Expected Files:** `[path/]`, `[file.py]`
- **Implementation Notes:** [Important rules or constraints]
- **Tests Required:** [What tests must be added or updated]
- **Verification:** `pytest ...` / manual check
- **Done Criteria:** [Conditions for completion]

#### Task [Number].[Number]: [Task Name]
- **Goal:** [Describe the task objective]
- **Scope:** [What is included and excluded]
- **Expected Files:** `[path/]`, `[file.py]`
- **Implementation Notes:** [Important rules or constraints]
- **Tests Required:** [What tests must be added or updated]
- **Verification:** `pytest ...` / manual check
- **Done Criteria:** [Conditions for completion]

### Deliverables

- [ ] [Deliverable 1]
- [ ] [Deliverable 2]

### Verification

```bash
# Example verification commands
pytest
python manage.py runserver
```
```

---

## 8. Code Commenting & Documentation

- **Docstrings:** Use concise `"""Docstring content"""` for classes and complex functions.
- **Logic Comments:** Explain why a decision exists, not what the line literally does.
- **Section Headers:**
  - **Python/Bash:** `# -- Header Name`
  - **HTML:** `<!-- --#-- Header Name -->`
  - **CSS/JS:** `/* --#-- Header Name */`
- **README Rule:** The README must reflect the actual current project state, not aspirational status presented as done.

---

## 9. Frontend & Asset Architecture

- **Static Structure:**
  - `static/css/`
  - `static/js/`
  - `static/images/`
- **Template Structure:**
  - `templates/`
  - `templates/__snippets__/`
  - `templates/components/`
- **Responsiveness:** UI must work on mobile, tablet, and desktop.
- **Design Rule:** Prefer deliberate, maintainable custom styling over rushed or inconsistent UI choices.
- **Progressive Interactivity Rule:** If using HTMX or JavaScript enhancements, the HTML structure must remain understandable and maintainable.

---

## 10. Naming Conventions

- **Files:** Lowercase with underscores where appropriate
- **CSS Classes:** Kebab-case
- **Python Classes:** PascalCase
- **Functions and Variables:** snake_case
- **Branches:** Lowercase, hyphen-separated
- **User-Facing Labels:** Clear, professional wording

---

## 11. Testing & Quality Assurance

- **Primary Tooling:** `pytest` and `pytest-django`
- **Test Location:** Prefer `app/tests/` or clearly organized test modules
- **Feature Rule:** No feature is complete without tests
- **Regression Rule:** Every bug fix should include a regression test where practical
- **Coverage Goal:** Target strong coverage on changed logic, especially business-critical flows
- **Pre-Commit Quality Gate:** Use `Black`, `Flake8`, and `Isort` through `pre-commit`
- **Verification Discipline:** Run the smallest relevant test set during iteration, then run broader verification before merge

---

## 12. Deployment Standards

- **Environment Parity:** Use environment-specific settings from the start, such as `base.py`, `dev.py`, and `prod.py`
- **Secrets Management:** Use environment variables and never commit secrets
- **Static Assets:** Use a production-safe static asset strategy such as `WhiteNoise` when applicable
- **Production Readiness:** Deployment work must include verification for settings, allowed hosts, static handling, and background task requirements if used

---

## 13. Review Standards

- **Reviewer Focus:** Review for bugs, regressions, security issues, architectural drift, and missing tests
- **Review Order:** Findings first, summary second
- **Blocking Rule:** If verification is missing or risk is unacceptably high, do not mark the task or phase as done
- **Documentation Check:** Ensure README, setup steps, and environment instructions still match the codebase after meaningful changes

---

## 14. Minimal Project Setup Checklist

Use this checklist when starting a new project:

- [ ] Virtual environment created
- [ ] Dependency files created
- [ ] Django project or app scaffold created
- [ ] Settings split into `base/dev/prod`
- [ ] `.env.example` created
- [ ] `.gitignore` created
- [ ] `pytest` configured
- [ ] `pre-commit` configured
- [ ] README initialized
- [ ] Initial phase plan defined
- [ ] Each phase split into tasks before implementation starts

---

*Constitution Version: 2.0 (Starter with Phase-Task Methodology)*
