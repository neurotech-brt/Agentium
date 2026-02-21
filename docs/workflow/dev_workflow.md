# Full Stack Developer Workflow

> A professional, repeatable pattern for building features and fixing bugs using AI agents and AI chatbots — without losing control of quality, correctness, or your codebase.

---

## Core Principles Before You Start

- **You are the architect. AI is the contractor.** AI executes; you decide.
- **Never let AI write code you don't understand.** If you can't review it, you can't own it.
- **Context is everything.** The quality of AI output is directly proportional to the context you provide.
- **One subtask at a time.** Scope creep kills AI-assisted sessions. Keep each AI interaction tightly bounded.
- **Always work on a branch.** Never let AI agents touch `main` or `production` directly.

---

## Step 1 — Identify & Prioritize the Subtask

**Goal:** Know exactly what you're working on before anything else.

Break the larger feature or bug into the smallest independently completable unit of work. A subtask should be something you can finish in one focused session (ideally under 2 hours).

**Ask yourself:**

- What is the single next thing that needs to exist or be fixed?
- Does this subtask have hard dependencies on unfinished work? If yes, do that first.
- Is this a UI change, a data/API change, a logic change, or an infra change? Keep these separate where possible.

**AI tip:** Paste your full task list or backlog into a chatbot and ask it to help prioritize by dependency order and risk. It's good at surfacing hidden dependencies you might miss.

**Output of this step:** A single, clearly scoped subtask statement.

> Example: _"Add server-side validation to the `/api/users/register` endpoint for email format and password strength, and return structured error responses."_

---

## Step 2 — Define the Expected Output

**Goal:** Know what "done" looks like before writing a single line of code.

Define the expected output concretely — what will exist, what will behave differently, and what the user or consumer of the code will experience.

**Define:**

- What is the visible/testable end result? (UI state, API response shape, database record, log output)
- What are the success criteria? (What must be true for this to be considered complete?)
- What is explicitly out of scope for this subtask?

**Do this yourself or with AI:** Paste your subtask statement into a chatbot and ask: _"What should the expected inputs, outputs, and observable behaviors be for this feature? Give me a concrete specification."_ Refine it until it's accurate.

**Output of this step:** A short specification — 5 to 15 lines describing inputs, outputs, and acceptance criteria.

---

## Step 3 — Plan the Implementation & Identify Risks

**Goal:** Think before you code. Catch problems on paper, not in production.

Map out how you'll implement the subtask. This is where you think about architecture, data flow, and what could go wrong.

**Cover these areas:**

**Implementation approach:**

- Which files, modules, or services will change?
- What new code needs to be created vs. what existing code needs to be modified?
- Are there existing patterns in the codebase you should follow?

**Edge cases to consider:**

- Empty inputs, null values, very large inputs
- Concurrent requests or race conditions
- Auth/permission edge cases
- Network failures or timeouts (for external calls)
- Partial failure states (what if step 2 of 3 fails?)

**Breaking change prevention:**

- What existing functionality could this change affect?
- Are there other consumers of the code you're modifying (other endpoints, other components, shared utilities)?
- Do you need a feature flag to safely roll this out?
- Is a database migration involved? Is it backward compatible?

**AI tip:** Give the chatbot your current implementation and your plan, then ask: _"What edge cases am I missing? What could break in the existing system if I make these changes?"_ This is one of the highest-value uses of AI in the workflow.

**Output of this step:** A short risk list and a confirmed implementation approach.

---

## Step 4 — Write the Detailed Step-by-Step Plan

**Goal:** Create a concrete, ordered todo list that you or an AI agent can execute without ambiguity.

This is your implementation blueprint. Write it out as numbered steps, specific enough that each step is one clear action. Include testing steps inline — don't treat testing as an afterthought.

**Template for each step:**

```
[ ] Action: <what to do>
    File(s): <which files are affected>
    Notes: <any constraints, patterns to follow, or gotchas>
    Test: <how to verify this step worked>
```

**Example plan:**

```
[ ] 1. Add Zod validation schema for registration payload
       File: src/validators/user.validator.ts
       Notes: Match the existing schema pattern in auth.validator.ts
       Test: Unit test with valid and invalid inputs

[ ] 2. Apply validator middleware to POST /api/users/register
       File: src/routes/user.routes.ts
       Notes: Use the existing validateRequest middleware wrapper
       Test: Manual curl with missing fields should return 400

[ ] 3. Update error response handler to include field-level errors
       File: src/middleware/errorHandler.ts
       Notes: Must remain backward compatible with existing error shape
       Test: Existing error handler tests still pass

[ ] 4. Write integration test for the full registration flow
       File: tests/integration/user.register.test.ts
       Test: Cover valid registration, duplicate email, invalid password, malformed JSON

[ ] 5. Update API documentation
       File: docs/api/users.md
       Test: Review only
```

**AI tip:** Give a chatbot your subtask spec and risk notes from Steps 2–3, and ask it to generate this todo list for you. Then review and edit it — AI often writes plans that skip testing or assume context it doesn't have.

**Output of this step:** A complete, numbered implementation plan with inline test steps.

---

## Step 5 — Implement

**Goal:** Execute the plan, using AI to accelerate without losing oversight.

Work through your Step 4 plan item by item. Do not skip ahead or let AI make decisions outside the scope of the current step.

**If implementing yourself:**

- Follow the plan. If you deviate, update the plan first.
- Commit frequently with meaningful messages (one logical change per commit).

**If using an AI agent (Cursor, Copilot, Claude Code, etc.):**

- Give the agent one step at a time, not the entire plan at once.
- Always provide full context: the relevant files, the existing patterns, and exactly what you want.
- After each agent action, read the diff before accepting it. Do not blindly accept AI-generated code.
- If the agent goes off-plan, stop it, re-scope the prompt, and restart that step.

**Prompt pattern for AI agents:**

> _"Here is the current state of [file]. I need you to [specific action from plan]. Follow the pattern used in [reference file]. Do not change anything outside of [scope]. Here are the constraints: [constraints from your plan]."_

**Red flags to watch for:**

- AI removing or refactoring code outside the requested scope
- AI adding dependencies you didn't ask for
- AI "solving" a problem differently than your plan without explaining why
- AI generating code that touches shared utilities or database schemas unexpectedly

**Output of this step:** Implemented, committed code — one step at a time.

---

## Step 6 — Test All Cases

**Goal:** Verify the implementation matches the spec and hasn't broken anything else.

Testing is not optional and it is not the last thing you do — it runs alongside every step. But here you do a final comprehensive pass.

**Testing checklist:**

**Unit tests:**

- Does the new logic handle all expected inputs correctly?
- Are all edge cases from Step 3 covered?
- Do existing unit tests still pass?

**Integration tests:**

- Does the full flow work end-to-end?
- Test the happy path, then every failure/edge case path.

**Regression check:**

- Run the full test suite. Investigate any new failures — do not ignore them.
- Manually test any adjacent features that share code with your changes.

**Manual testing:**

- Verify the actual behavior in a browser or API client (Postman, curl, etc.)
- Test on realistic data, not just the minimal example that passes.

**If using AI agents for testing:**

- Ask the agent to generate test cases from your spec (Step 2) and edge cases (Step 3).
- Review every generated test — AI commonly generates tests that only test the happy path or that mock too aggressively and don't catch real bugs.
- Ask the agent: _"What test cases would catch regressions in the existing system caused by these changes?"_

**Output of this step:** All tests written and passing. No regressions.

---

## Step 7 — Verify & Close

**Goal:** Confirm the work is truly complete and leave a clear record of it.

Do a final structured review before marking the task done.

**Completion checklist:**

```
[ ] All items in the Step 4 plan are checked off
[ ] All tests pass (unit, integration, regression)
[ ] Code has been reviewed (self-review at minimum, peer review preferred)
[ ] No debug code, console.logs, or temporary hacks left in
[ ] Relevant documentation updated (API docs, README, inline comments)
[ ] Any TODOs or deferred items are logged in the backlog with context
[ ] Branch is clean and ready to merge or open for PR
[ ] PR description clearly states: what changed, why, and how to test it
```

**Mark completion clearly:**

- Update the ticket/issue with a summary of what was done and any decisions made.
- In your PR or commit message, reference the task and write a human-readable summary.
- If working with a team, call out anything the reviewer needs to pay special attention to.

**AI tip:** Paste your diff into a chatbot and ask: _"Review this code change. Are there any bugs, missing edge cases, security issues, or style inconsistencies? Does it match this spec: [paste spec]?"_ This is a cheap second opinion before code review.

**Output of this step:** Task closed with full documentation. Ready to move to the next priority.

---

## Quick Reference Card

| Step              | What You're Doing                   | Primary Tool     |
| ----------------- | ----------------------------------- | ---------------- |
| 1. Prioritize     | Pick the next right subtask         | You + AI chatbot |
| 2. Define Output  | Write the spec                      | You + AI chatbot |
| 3. Plan & Risk    | Map implementation, find edge cases | You + AI chatbot |
| 4. Write Plan     | Create step-by-step todo with tests | You + AI chatbot |
| 5. Implement      | Execute the plan step by step       | You + AI agent   |
| 6. Test           | Full test coverage + regression     | You + AI agent   |
| 7. Verify & Close | Final review and documentation      | You              |

---

## Common Pitfalls to Avoid

**Skipping Steps 2–4 and jumping straight to coding.** This is where AI-assisted development goes wrong most often. AI agents work best when they have a tightly scoped, well-specified task. Vague prompts produce vague code.

**Giving AI agents too much context at once.** Long prompts with many files and many requirements produce unfocused results. One step, one concern, one prompt.

**Not reading AI diffs.** AI agents will sometimes quietly refactor, rename, or remove things adjacent to what you asked for. Always read the full diff.

**Treating passing tests as proof of correctness.** AI-generated tests often test the implementation rather than the requirement. Write tests against the spec, not the code.

**Letting AI accumulate context debt.** In long AI chat sessions, earlier context gets degraded. For long implementations, start a fresh session per major step and re-provide context explicitly.

**Merging without a human review pass.** Even if AI wrote the code and AI tested the code, a human should read the final diff. You are responsible for what goes into your codebase.

---

## Suggested Tools by Role

| Task                        | Recommended Tools                |
| --------------------------- | -------------------------------- |
| Planning & spec writing     | Claude, ChatGPT, Gemini          |
| Code generation (in-editor) | Cursor, GitHub Copilot, Cline    |
| Agentic coding (multi-file) | Claude Code, Cursor Agent, Devin |
| Code review assistance      | Claude, ChatGPT + diff paste     |
| Test generation             | AI agent with spec as context    |
| Documentation               | AI chatbot with code + spec      |

---

_Last updated: February 2026_
