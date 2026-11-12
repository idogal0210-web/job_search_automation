# Authoring Multi-Operation Site Specs

Use the `api-anything` CLI (`npx -y api-anything <command>`) when authoring multi-operation site specs, refining extraction recipes, or learning writes. Run `api-anything <command> --help` for full flag details.

## 1. Agree on Operations

Before capturing traffic:
- Identify which questions need answering, which inputs vary per call, which output fields are required, and whether authentication is needed.
- Define one operation per question shape: `name(inputs) -> fields`, along with what is out of scope.

## 2. Capture

```bash
npx -y api-anything capture "https://site.com/search?q=example" --example q=example --outline
```

- Choose the candidate request that `carries` the example input and whose URL or `operationName` matches the target data.
- Use `--outline` to obtain ready `--extract`/`--pick`, `--embedded`, or `--html` recipes; use `inspect <captureId> [<requestId>]` only if `--outline` leaves ambiguity.
- If `list.count` is smaller than what appears on the page, script hydration is filling it; select the underlying JSON XHR/fetch request.
- If the page requires typing into a search box, capture with `--steps` to trigger the autocomplete/search endpoint.
- If an SPA only fires the request on client-side route transition, add `--soft-from <another-page-url>`.
- Prefer server-rendered `document` or `schema.org` JSON-LD on detail pages when available, as they survive minor UI redesigns.

## 3. Add Operation

```bash
npx -y api-anything add <site> <op> --trigger "https://site.com/search?q={q}" \
  --example q=alpha --example2 q=beta --pick title,url
```

- Provide a second example (`--example2`) whose response must differ from the first. An `unproven` warning indicates the server may be ignoring that parameter.
- For pickers or radio filters, `--enum` must list the site's complete option set, not only the example value.
- If `add` picks the wrong network request, re-run with `--from <captureId> --pick-request <requestId>` (no second browser launch needed).
- Inspect `warnings` and `preview` output before finalizing.

## 4. Check & Verify

1. Call the operation with a fresh public value not used as an example and compare `data` against the live site.
2. Add deterministic `check` assertions using public values: one `result` check exercising optional filters so at least one row is filtered out, and one `empty` check.
3. Run `npx -y api-anything verify <site>` and resolve any failures or `inconclusive` cases following `next`.
4. Preview before sharing with `npx -y api-anything publish <site> <op>`; pass `--yes` only with explicit user approval.
