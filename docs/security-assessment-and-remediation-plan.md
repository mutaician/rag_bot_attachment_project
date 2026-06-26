# Security Assessment and Remediation Plan

Audience: Student developers.

This document is intentionally direct. These are not theoretical concerns; several are immediately exploitable by any authenticated user.

---

## Severity legend

- **P0 / Critical**: must fix before real use
- **P1 / High**: fix next
- **P2 / Medium**: important hardening

---

## P0-1: Broken Access Control (IDOR) across conversations

### What is wrong
Authentication exists (cookie session), but authorization scoping is missing in conversation queries.

Observed behavior from code paths:
- `GET /conversations` returns all conversations
- `GET /conversations/{id}` fetches by id without user/team ownership check
- `DELETE /conversations/{id}` deletes by id without ownership check
- `POST /chat` accepts `conversation_id` and validates existence, not ownership

### Why this is severe
Any logged-in user can read, hijack, and delete another user’s chat history.

### Practical exploit path
1. User A creates conversations.
2. User B logs in normally.
3. User B requests conversation list and gets IDs/titles not belonging to them.
4. User B reads and deletes those conversations.

### Repro examples

```bash
# 1) Login as user B (captures cookie)
curl -i -c cookie.txt -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"user_b","password":"password"}'

# 2) List all conversations (should be scoped, but currently global)
curl -b cookie.txt http://localhost:8000/conversations

# 3) Read a specific conversation (including another user's)
curl -b cookie.txt http://localhost:8000/conversations/<victim_conversation_uuid>

# 4) Delete victim conversation
curl -i -b cookie.txt -X DELETE http://localhost:8000/conversations/<victim_conversation_uuid>
```

### Fix
- Add ownership/team columns and policy.
- Pass current user scope into DB methods.
- Enforce WHERE clauses by owner/team on list/get/delete and chat conversation resolution.
- Add tests that user B gets 404/403 on user A resources.

---

## P0-2: Broken Access Control likely affecting document operations

### What is wrong
Document endpoints are authenticated but not scoped by owner/team in query methods.

### Why this is severe
Any authenticated user can enumerate and delete documents outside their authorization boundary.

### Repro examples

```bash
# List documents (expected: own/team docs only)
curl -b cookie.txt http://localhost:8000/documents

# Soft delete someone else's doc
curl -i -b cookie.txt -X DELETE \
  http://localhost:8000/documents/<victim_document_uuid>

# Hard delete someone else's doc
curl -i -b cookie.txt -X DELETE \
  'http://localhost:8000/documents/<victim_document_uuid>?hard=true'
```

### Fix
Same as conversations: strict authorization scoping at DB layer + route layer.

---

## P0-3: Upload memory DoS and parser abuse

### What is wrong
Upload handler reads entire file into memory (`await upload.read()`) before writing to disk.
No explicit server-side file size cap in FastAPI path.

### Why this is severe
Single oversized request can consume memory and degrade or crash service.
Crafted PDFs can force expensive parser work.

### Practical exploit path
- Send very large multipart uploads repeatedly.
- Worker/API memory and CPU spike; requests queue/fail.

### Repro idea

```bash
# Example: upload a very large file repeatedly
curl -b cookie.txt -F 'files=@large.pdf' http://localhost:8000/documents/upload
```

### Fix
- Stream uploads in chunks to disk.
- Enforce max size in app code (not only nginx).
- Cap PDF page count and parsing time.
- Add request rate limits for upload endpoint.

---

## P0-4: No brute-force protection on login

### What is wrong
`POST /auth/login` has no rate limiting, lockout, or backoff.

### Why this is severe
Enables rapid online password guessing and credential stuffing.

### Repro idea
Automate repeated credential attempts from one host.

### Fix
- Per-IP + per-username throttling.
- Temporary lockout or exponential delay after failures.
- Security logging/alerting for failed auth spikes.

---

## P1-1: Any authenticated user can switch global LLM mode

### What is wrong
`PUT /system/llm` changes deployment-wide behavior and is available to any signed-in user.

### Why this matters
Operational sabotage / accidental outages / unexpected cloud usage and cost.

### Fix
Require admin role for global system setting changes.

---

## P1-2: Internal error leakage in chat SSE

### What is wrong
SSE error events include raw exception text.

### Why this matters
May leak internals (stack detail, infra hints, model/backend failures).

### Fix
Return generic client error messages; log detailed exceptions server-side.

---

## P1-3: Authorization model mismatch with project brief

### What is wrong
Brief mentions per-user history and internal tool controls; implementation currently behaves as globally shared in core queries.

### Why this matters
Policy expectations and implementation differ — dangerous in org context.

### Fix
Define and implement explicit model: per-user, per-team, or role-based shared spaces.

---

## P2: Additional hardening and resilience

- Add pagination and bounds on list endpoints.
- Add optimistic locking or transactional strategy for filename version race handling.
- Add CSRF protections for cookie-authenticated state-changing endpoints.
- Add audit trail (who deleted what, who changed LLM mode, when).
- Add content-security headers and stricter production defaults.

---

## Ready-to-paste PR review summary

```markdown
Requesting changes before merge due to critical security blockers:

P0:
1) Broken access control (IDOR) in conversations and likely documents
2) Upload endpoint allows memory/CPU DoS conditions
3) Login endpoint has no brute-force protections

P1:
1) Global LLM mode switch should be admin-only
2) Chat SSE leaks internal errors

Please fix P0 items with regression tests, then request re-review.
```

---

## Ready-to-paste inline comment snippets

### On conversation list/get/delete routes
```markdown
P0: AuthN exists, but authZ scoping is missing. This query must be constrained by current user/team; otherwise any authenticated user can read/delete others' data.
```

### On chat conversation resolution
```markdown
P0: `conversation_id` existence check is not enough. Validate ownership/team membership before loading or appending messages.
```

### On upload read path
```markdown
P0: Avoid `await upload.read()` for full-file memory load. Stream to disk in chunks and reject files above a strict server-side max size.
```

### On login handler
```markdown
P0: Missing brute-force defenses (rate limits/lockout/backoff). Please add per-IP + per-username controls and tests.
```

### On system LLM mode route
```markdown
P1: This mutates deployment-wide state and should require admin role.
```

---

## Quick note

Treat the P0 findings as release blockers. You should demonstrate:
1) threat model,
2) secure-by-default authorization boundaries,
3) regression tests proving isolation between users.
