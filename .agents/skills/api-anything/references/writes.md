# Write Operations Policy

Write operations (posting, liking, sending, submitting applications, purchasing) modify external state on the user's account. Only learn or send writes on the user's own account and only when explicitly requested.

## 1. Learning a Write Safely

- Learn writes via `capture` and `add --write` (see [authoring.md](authoring.md)). `api-anything` aborts the write request inside the browser capture so the action is not actually submitted during learning.
- Never use `--match method=POST` to force-pin an unknown write as a read, because pinned read requests execute for real on every learning run. Only pin idempotent `POST` search endpoints.
- For multi-step checkouts or application forms, stop before payment or final submission; let the user complete sensitive/payment fields manually.

## 2. Executing a Write

- The project MCP server disables writes by default (`--allow-writes` is not enabled). Executing writes requires explicit user approval and either `--allow-writes` on the CLI or a user-approved writes-enabled server configuration.
- Before sending a real write, run `npx -y api-anything call <site> <op> ... --dry` to verify the exact request payload, target IDs, and text.
- Inspect the returned `write` status: only `applied` confirms the write landed. After `accepted` or `may_have_applied`, never automatically retry; ask the user to verify on the site.
- Duplicate writes within 10 minutes are blocked with `class: "duplicate"`. Only pass `--again` / `again: true` after the user verifies the action did not take effect and explicitly asks to resend.

## 3. Verification via Readback

```bash
npx -y api-anything readback <site> <write-op> <read-op> [k={param}] --find field={value}
```

Verify using a unique value produced by the write (such as an explicit title or returned ID), not a generic shared status.
