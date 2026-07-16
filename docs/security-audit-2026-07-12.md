# EVOLV Platform Security Audit — 2026-07-12

**Scope:** `API/` (FastAPI app + 18 routers), `Agents/`, `utils/`,
`scripts/`, `react-platform/src/` (XSS + secrets surface only),
root config.
**Method:** Full-codebase sweep with fixes applied in the same
pass. All changes compile (`py_compile`), the app imports cleanly
(`import API.main`), and the auth gate was functionally smoke-
tested (dev passthrough / 401 without key / 401 wrong key /
200 correct key / sanitizer traversal + header-injection cases).
**Status:** All Critical/High findings FIXED. Two architectural
items REPORTED for a future sprint.

---

## Executive summary — top 5 risks for a pharma security review

1. **No API authentication (FIXED)** — every endpoint was
   publicly callable. An optional platform-wide API-key gate now
   covers all routes: set `EVOLV_API_KEY` and every request must
   carry a matching `X-API-Key` header (constant-time compare,
   scoped KeyStore keys still honoured). Unset = dev mode with a
   loud startup warning.
2. **Unbounded user input reaching PDF/file generation (FIXED)**
   — 63 `max_length` constraints added across all request models;
   filename components are sanitized against path traversal and
   `Content-Disposition` header injection at 6 call sites.
3. **Raw exception details returned to clients (FIXED)** — 28
   endpoints returned `str(exc)` to the caller. Clients now get a
   generic message + CSV-error code; full detail goes to the
   server log / audit trail only.
4. **CORS defaults were broad (FIXED)** — allow-list is now
   env-controlled (`EVOLV_CORS_ORIGINS`); wildcard `*` is
   rejected outright. Defaults cover local dev ports only
   (5173/5174/5179/5180/3000/8501).
5. **Audit trail rows are individually hashed but not chained
   (REPORTED)** — see finding SEC-9.

---

## Findings

| ID | Severity | Location | Finding | Status |
|----|----------|----------|---------|--------|
| SEC-1 | **Critical** | `API/main.py` (all routes) | No authentication on any endpoint | **FIXED** — `API/security.py:require_platform_key` applied app-wide via `FastAPI(dependencies=[...])` |
| SEC-2 | **High** | 18 routers | Unbounded string fields in request models flow into PDFs, filenames, and stores | **FIXED** — 63 Pydantic `Field(max_length=…)` constraints |
| SEC-3 | **High** | `exports.py`, `bap.py`, `audit.py`, `traceability.py`, `trustworthiness.py`, `release.py` | User-supplied values used in filenames / `Content-Disposition` headers (path traversal, CRLF header injection) | **FIXED** — `sanitize_filename_component()` at 6 call sites |
| SEC-4 | **High** | 28 endpoints + `job_store.py` | Raw `str(exc)` leaked to clients (stack detail, paths, internals) | **FIXED** — generic client messages with CSV codes; `logger.exception` server-side |
| SEC-5 | **Medium** | `API/main.py` CORS | 12 hard-coded origins incl. Streamlit; no production override | **FIXED** — `get_cors_origins()` allow-list, env override, wildcard rejected |
| SEC-6 | **Medium** | `governance.py` admin surface | Key-metadata endpoint lacked per-endpoint key check | **FIXED** — `require_api_key` dependency added |
| SEC-7 | **Low** | repo-wide | Secrets scan: only `.streamlit/secrets.toml.example` matches key patterns (placeholders only); `.gitignore` covers `.env*` and `secrets.toml` | **PASS** — no action |
| SEC-8 | **Low** | `react-platform/src` | XSS surface: zero `dangerouslySetInnerHTML` usages | **PASS** — no action |
| SEC-9 | **Medium** | `Agents/integrity_manager.py` | Audit rows carry per-row SHA-256 (tamper-evident per record) but each hash does not include the previous row's hash — silent row deletion/reorder would not break a chain. File is append-only by code, not by construction. | **FIXED 2026-07-16 (Sprint 45)** — every new row's hash chains onto the previous row's hash; legacy rows verify against the original formula; `verify_audit_chain()` + `scripts/verify_audit_chain.py` + `GET /audit/verify-chain` detect edits, deletions, and reorders (6 evals in the Trusted Evals suite). Residual: tail truncation requires external head-hash anchoring — documented in the verifier output. |
| SEC-10 | **Info** | dependencies | fastapi/uvicorn/pydantic versions not pinned to CVE-audited releases; no `pip-audit` in CI | **FIXED 2026-07-16 (Sprint 46)** — pip-audit sweep found 13 vulnerable packages (incl. starlette 0.52.1, pypdf 6.7.5 ×7 advisories, urllib3, tornado, requests); all upgraded, environment now audits clean, platform verified post-upgrade (API imports + 131/131 evals). Security floors pinned in `requirements.txt`; blocking `dependency-audit` (pip-audit) and `trusted-evals` (131 checks, stdlib-only) jobs added to `.github/workflows/compliance-check.yml`. |

## Fix inventory (files changed)

- **New:** `API/security.py` — `require_platform_key` (401 gate,
  constant-time compare, KeyStore fallback),
  `sanitize_filename_component`, `get_cors_origins`,
  `warn_if_auth_disabled`; typed exceptions CSV-050/051/052.
- **Wired:** `API/main.py` — app-wide auth dependency, startup
  warning, CORS allow-list, error-message hardening.
- **Hardened:** all 17 routers + `API/job_store.py` (input
  limits, filename sanitisation, generic error responses).

## Deployment notes

```bash
# Production: REQUIRED before exposing beyond localhost
export EVOLV_API_KEY="<long random secret>"
export EVOLV_CORS_ORIGINS="https://app.evolifeval.com"
```

The React frontend must send `X-API-Key` on every request once
the key is set (header is already in the CORS allow-headers).

## What a pharma security reviewer will still ask

- **Penetration test** — none performed; this was a code-level
  audit. Commission one before first production tenant.
- **SOC 2 / hosting model** — single-tenant on-prem vs. hosted
  SaaS changes the answer; document the deployment options.
- **Secrets management** — env vars are fine for pilots; move to
  a vault (Azure Key Vault / AWS SM) for production.
- **Audit-trail chaining** — close SEC-9 before positioning the
  trail as cryptographically append-only in sales material.
- **Session/user model** — the platform key authenticates the
  *client*, not the *user*; per-user identity currently arrives
  via `user_id` fields. A real IdP (SSO/SAML) is the enterprise
  expectation.
