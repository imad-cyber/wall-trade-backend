# WallTrade Backend — Architecture Migration Implementation Plan

> **Version:** 1.0  
> **Date:** 2026-06-27  
> **Author:** Principal Backend Architect  
> **Status:** Awaiting Approval  
> **Migration Duration:** ~12–18 weeks (phased, no freeze)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current Architecture Audit](#2-current-architecture-audit)
3. [Gap Analysis](#3-gap-analysis)
4. [Migration Strategy](#4-migration-strategy)
5. [Architecture Dependency Graph](#5-architecture-dependency-graph)
6. [Phase-by-Phase Implementation Plan](#6-phase-by-phase-implementation-plan)
7. [Risk Register](#7-risk-register)
8. [Testing Strategy](#8-testing-strategy)
9. [Rollback Strategy](#9-rollback-strategy)
10. [Technical Debt Register](#10-technical-debt-register)
11. [Future Expansion Opportunities](#11-future-expansion-opportunities)
12. [Final Migration Checklist](#12-final-migration-checklist)

---

## 1. Executive Summary

WallTrade is a fintech AI platform built on FastAPI, Next.js 15, Supabase, Capital Stake API, PSX Proxy, and OpenAI. The backend has a solid foundational skeleton (FastAPI factory pattern, `pydantic-settings`, structured JSON logging, Supabase integration, JWT auth), but it is in **early-stage architecture** — meaning most external provider integrations are stubs, business logic lives directly inside routers, and no AI pipeline, repository layer, or observability infrastructure exists yet.

This is an **ideal migration window**: the codebase is small enough to refactor safely, but the architecture decisions made now will determine the system's scalability ceiling for the next 3–5 years.

### Migration Mandate

| Principle | Commitment |
|---|---|
| **Incremental** | Every phase leaves the application fully deployable |
| **Backward Compatible** | No existing API contract broken without a versioned route |
| **Low Risk** | Extract and wrap, never rewrite wholesale |
| **Test Driven** | Tests are written before or alongside every phase |
| **Feature Safe** | Development on new features can continue in parallel |
| **History Preserving** | Prefer `git mv` over delete+create |

### What Changes and What Stays

| What Stays | What Evolves |
|---|---|
| FastAPI as BFF framework | `app/` flat module layout → layered directory structure |
| Pydantic + pydantic-settings | `app/config/settings.py` → `app/core/config.py` (consolidation) |
| Supabase as the database | `app/database/` + `SupabaseDBService` → `providers/supabase/` + `repositories/` |
| JSON structured logging | `app/core/logging_config.py` → `app/core/logging.py` (enhanced) |
| Exception hierarchy | `app/core/exceptions.py` → expanded hierarchy + middleware handlers |
| JWT auth flow | `app/auth.py` (God file) → `app/auth/` package (split) |
| `ApiResponse` envelope | `schemas_walltrade.ApiResponse` → `api/v1/schemas/envelope.py` (generic `APIResponse[T]`) |
| Existing 10 endpoints | Untouched during infrastructure phases; refactored in Phase 9 |

---

## 2. Current Architecture Audit

### 2.1 Directory Structure (As-Is)

```
Wall-Trade-Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # App factory — good pattern
│   ├── auth.py                     # ⚠️  God file: AuthService + 2 Depends + JWT + bcrypt
│   ├── constants.py                # Disconnected from Settings
│   ├── database.py                 # Stub re-exporter (1 line)
│   ├── dependencies.py             # ⚠️  Mixed concerns: DB + settings + auth guard + Supabase client creation
│   ├── api/
│   │   └── v1/
│   │       ├── router.py           # Good aggregation pattern
│   │       ├── schemas.py          # Almost empty (deprecated)
│   │       ├── schemas_walltrade.py # ⚠️  Monolithic schemas: DTOs + responses + domain objects mixed
│   │       └── endpoints/          # 10 endpoint files
│   │           ├── analysis.py     # ⚠️  Business logic + DB call + streaming stub inside router
│   │           ├── companies.py    # Provider stub — not implemented
│   │           ├── health.py       # Thin — correct
│   │           ├── macro.py        # Direct SupabaseDBService call from router
│   │           ├── market_feel.py  # Direct SupabaseDBService call from router
│   │           ├── portfolios.py   # Direct SupabaseDBService call from router
│   │           ├── prices.py       # Provider stub — not implemented
│   │           ├── script_history.py # Direct SupabaseDBService call from router
│   │           ├── sector_feel.py  # Direct SupabaseDBService call from router
│   │           └── trades.py       # Direct SupabaseDBService call from router
│   ├── config/
│   │   └── settings.py             # ✅ Pydantic BaseSettings singleton — well implemented
│   ├── core/
│   │   ├── __init__.py             # Re-exports logging + exceptions
│   │   ├── exceptions.py           # ✅ Good hierarchy — missing AIProviderError, RateLimitError
│   │   └── logging_config.py       # ✅ JSON + file logging — missing request_id injection
│   ├── database/
│   │   └── connection.py           # ⚠️  Double-singleton pattern (class + global variable)
│   ├── models/
│   │   └── schemas.py              # ⚠️  Orphaned: ResponseSchema not used by active endpoints
│   ├── routes/                     # ⚠️  Orphaned legacy router (not registered in main)
│   │   └── company.py
│   ├── services/
│   │   ├── base_service.py         # Thin logger wrapper — adds minimal value
│   │   ├── capital_stake.py        # ⚠️  Stub: inherits DB client but does nothing; misnamed (not a provider)
│   │   ├── psx_service.py          # ⚠️  Stub: inherits DB client but does nothing; misnamed (not a provider)
│   │   └── supabase_db.py          # ⚠️  Proto-repository: contains domain queries mixed with generic CRUD
│   └── utils/
│       ├── api.py                  # Barely used
│       ├── decorators.py           # ✅ retry + timing decorators — not integrated with tenacity
│       └── responses.py            # ⚠️  Parallel response layer unused by active endpoints
├── tests/
│   ├── test_auth.py                # Minimal stub
│   ├── test_config.py              # Minimal stub
│   └── test_main.py                # Health check + 404 test
├── conftest.py                     # Root conftest (empty)
├── requirements.txt                # Pinned but lacks: httpx extras, tenacity, apscheduler, opentelemetry
├── pyproject.toml                  # ✅ Black, isort, mypy, pytest configured
└── Dockerfile / docker-compose.yml # Present but not audited for correctness
```

### 2.2 Dependency Graph (As-Is)

```
main.py
  └─→ config/settings.py          (get_settings)
  └─→ core/logging_config.py      (setup_logging, get_logger)
  └─→ core/exceptions.py          (AppException)
  └─→ database/connection.py      (get_db_manager)
  └─→ api/__init__.py             (api_router)

api/v1/endpoints/*.py
  └─→ auth.py                     (get_current_supabase_user)  ← direct import
  └─→ config/settings.py          (get_settings)               ← direct call (not DI)
  └─→ dependencies.py             (get_db_dependency)
  └─→ services/supabase_db.py     (SupabaseDBService)          ← instantiated inside endpoint

services/supabase_db.py
  └─→ core/logging_config.py
  └─→ core/exceptions.py

dependencies.py
  └─→ auth.py                     (security)
  └─→ database/connection.py      (get_db_client)
  └─→ config/settings.py          (get_settings)
  └─→ supabase (direct import)    ← creates Supabase client inline

auth.py
  └─→ config/settings.py          (get_settings — called inside function, not injected)
  └─→ core/logging_config.py
```

### 2.3 Identified Anti-Patterns

| # | Anti-Pattern | Location | Severity |
|---|---|---|---|
| AP-01 | **God file** | `app/auth.py` — AuthService + JWT + bcrypt + two FastAPI `Depends` functions | High |
| AP-02 | **Business logic in router** | `analysis.py` — cache check, config validation, SSE event generation all inside endpoint | High |
| AP-03 | **Direct DB access in routers** | `macro.py`, `portfolios.py`, `trades.py`, `market_feel.py`, `script_history.py` — `SupabaseDBService` instantiated at call site | High |
| AP-04 | **Double singleton** | `database/connection.py` — `DatabaseManager.__new__` + `_db_manager` global variable (two separate singleton mechanisms) | Medium |
| AP-05 | **Supabase client created per-request** | `dependencies.py:44` — `create_client()` inside every authenticated request | High |
| AP-06 | **Settings accessed imperatively** | `get_settings()` called directly in `auth.py:168`, `companies.py:13`, `prices.py:14` — bypasses FastAPI DI | Medium |
| AP-07 | **Orphaned code** | `app/routes/company.py` — not wired to any router; `app/models/schemas.py` — not used by active endpoints; `app/utils/responses.py` — not used | Low |
| AP-08 | **Parallel schema systems** | `models/schemas.ResponseSchema` vs `schemas_walltrade.ApiResponse` — two response envelope types in use | Medium |
| AP-09 | **Mixed domain in monolith schema file** | `schemas_walltrade.py` — DTOs (TradeCreate), domain models (AnalysisObject), response envelopes (ApiResponse), and profile schema (Profile) in one file | Medium |
| AP-10 | **No middleware for cross-cutting concerns** | No request ID injection, no timing middleware, no structured error context in logs | High |
| AP-11 | **Provider stubs misnamed as services** | `capital_stake.py`, `psx_service.py` — inherit `BaseService` (a logging wrapper), hold a `db_client`, but are external API clients | Medium |
| AP-12 | **No AI pipeline** | AI analysis endpoint is a stub — yields one static SSE event | Critical |
| AP-13 | **No centralized HTTP client** | No `httpx.AsyncClient` lifecycle management; providers will need to be written from scratch but without shared retry/timeout/tracing | High |
| AP-14 | **No observability** | No request context propagation, no Prometheus metrics, no OpenTelemetry | High |
| AP-15 | **No background tasks** | No APScheduler or equivalent; macro cache refresh, analysis cache cleanup, health checks are all absent | Medium |
| AP-16 | **Blocking Supabase client** | `supabase` library uses synchronous `postgrest` under the hood in current version — no `async` execution | High |
| AP-17 | **No type safety on DB results** | `SupabaseDBService` returns `dict[str, Any]` — no domain model mapping | Medium |
| AP-18 | **No cache abstraction** | Cache TTL is hardcoded inside `supabase_db.py:111` (24 hours) and not driven by Settings | Medium |
| AP-19 | **Missing exception types** | `AIProviderError`, `RateLimitError` absent from `core/exceptions.py` | Low |
| AP-20 | **Test coverage near zero** | 3 test files: health check, stub auth test, stub config test; no integration, no unit, no provider tests | High |

### 2.4 Architectural Strengths (Preserve)

| Strength | Location | Action |
|---|---|---|
| Factory pattern (`create_app`) | `main.py` | Keep — move lifespan out |
| Pydantic BaseSettings singleton | `config/settings.py` | Keep — move to `core/config.py` |
| JSON structured logging | `core/logging_config.py` | Keep — enhance with request_id |
| Exception hierarchy | `core/exceptions.py` | Keep — extend with missing types |
| v1 API versioning | `api/v1/` | Keep — already correct structure |
| Router aggregation | `api/v1/router.py` | Keep — good pattern |
| Supabase JWT validation | `auth.py` (get_current_supabase_user) | Keep — move to `auth/dependencies.py` |
| `_execute` APIError wrapper | `supabase_db.py` | Keep — promote to `repositories/base.py` |
| `@lru_cache` settings singleton | `config/settings.py` | Keep |
| `pyproject.toml` tooling | root | Keep |

---

## 3. Gap Analysis

### 3.1 Migration Matrix

| Current Component | Current Location | Target Location | Gap | Priority | Risk | Migration Strategy |
|---|---|---|---|---|---|---|
| App Settings | `app/config/settings.py` | `app/core/config.py` | Missing: `CAPITAL_STAKE_BASE_URL`, `AI_MODEL`, `AI_MAX_TOKENS`, `ANALYSIS_CACHE_TTL_HOURS`, `MACRO_CACHE_TTL_HOURS`, `DEFAULT_TIMEOUT_SECONDS`, `DEFAULT_MAX_RETRIES`, `ALLOWED_ORIGINS` | P1 | Low | Move file, add missing fields |
| Logging | `app/core/logging_config.py` | `app/core/logging.py` | Missing: request_id injection into log records | P1 | Low | Rename + extend with context filter |
| Exception hierarchy | `app/core/exceptions.py` | `app/core/exceptions.py` | Missing: `AIProviderError`, `RateLimitError`; existing handlers in `main.py` return non-envelope format | P1 | Low | Add types + standardize handlers |
| Lifespan | inline in `main.py` | `app/core/lifespan.py` | Missing: APScheduler registration | P2 | Low | Extract to module |
| CORS middleware | inline in `main.py` | `app/core/middleware.py` | Missing: Request ID injection, timing, auth middleware | P2 | Low | Extract + add new middleware |
| Auth (JWT/bcrypt) | `app/auth.py` | `app/auth/jwt.py` | Monolith file — needs split | P3 | Medium | `git mv` + split |
| Auth dependencies | `app/auth.py` | `app/auth/dependencies.py` | Same file | P3 | Medium | Extract Depends functions |
| Supabase auth wrapper | `app/auth.py` | `app/auth/supabase_auth.py` | `get_current_supabase_user` logic | P3 | Medium | Extract |
| Supabase client/pool | `app/database/connection.py` + `dependencies.py` | `app/providers/supabase/client.py` | Client created per-request; no async | P4 | High | Wrap in provider; fix per-request creation |
| Supabase executor | `services/supabase_db.py:_execute` | `app/providers/supabase/executor.py` | Partial — missing async | P4 | Medium | Extract + promote |
| AnalysisRepository methods | `services/supabase_db.py` | `app/repositories/analysis_repository.py` | Implicit — queries exist but no typed layer | P5 | Medium | Extract methods into typed repo |
| MacroRepository methods | `services/supabase_db.py` | `app/repositories/macro_repository.py` | Implicit — `get_latest_macro` is macro-domain | P5 | Medium | Extract |
| ProfileRepository | absent | `app/repositories/profile_repository.py` | Completely missing | P5 | Low | New file |
| BaseRepository | absent | `app/repositories/base.py` | Completely missing | P5 | Low | New file |
| Capital Stake client | `services/capital_stake.py` (stub) | `app/providers/capital_stake/client.py` | Stub only; no real HTTP calls | P6 | High | Rewrite as provider using `core/http.py` |
| PSX Proxy client | `services/psx_service.py` (stub) | `app/providers/psx_proxy/client.py` | Stub only; no real HTTP calls | P6 | High | Rewrite as provider |
| Centralized HTTP client | absent | `app/core/http.py` | Completely missing | P6 | Medium | New: httpx + tenacity |
| Domain models | absent | `app/domain/` | Completely missing | P7 | Medium | New: pure Pydantic models |
| Service layer | absent (routers call DB directly) | `app/services/` | Completely missing | P8 | High | Extract from routers |
| AI pipeline | stub in `analysis.py` | `app/ai/analysis_pipeline.py` | Completely missing | P9 | High | New module |
| AI streaming manager | stub in `analysis.py` | `app/ai/streaming.py` | Completely missing | P9 | High | New module |
| Prompt builder | absent | `app/ai/prompt_builder.py` | Completely missing | P9 | Medium | New module |
| OpenAI provider | absent | `app/providers/ai/openai_client.py` | Completely missing | P9 | Medium | New provider |
| Response envelope | `schemas_walltrade.ApiResponse` | `app/api/v1/schemas/envelope.py` | Not generic; no `meta` field (request_id, cache_hit, latency) | P4 | Medium | Extend + generify |
| API dependencies | `app/dependencies.py` | `app/api/v1/dependencies.py` | Mixed concerns; needs service factory functions | P8 | Medium | Split + expand |
| Observability context | absent | `app/observability/context.py` | Completely missing | P10 | Low | New: contextvars |
| Prometheus metrics | absent | `app/observability/metrics.py` | Completely missing | P11 | Low | New: prometheus_client |
| OTEL tracing | absent | `app/observability/tracing.py` | Completely missing | P11 | Low | New: opentelemetry |
| Background tasks | absent | `app/tasks/` | Completely missing | P12 | Low | New: APScheduler |
| FMP provider | absent | `app/providers/fmp/` | Completely missing | P6 | Medium | New provider |
| Test suite | 3 stub files | `tests/{unit,integration,api,providers}/` | Near zero coverage | All Phases | High | Progressive build-up |
| Utils decorators | `app/utils/decorators.py` | `app/utils/decorators.py` | Not integrated with tenacity; imports inside function bodies | Low | Low | Refactor |
| Orphaned code | `app/routes/`, `app/models/`, `app/utils/responses.py` | Deleted or merged | Dead code | Cleanup | Low | Delete in Phase 15 |

### 3.2 Schema/Contract Gaps

| Contract | Current | Target | Impact |
|---|---|---|---|
| Response format | `{"success": bool, "message": str, "data": Any}` | `{"success": bool, "data": T, "meta": {request_id, latency_ms, cache_hit}, "errors": []}` | Frontend must be updated |
| Error format | `{"success": false, "error_code": str, "message": str}` | `{"success": false, "data": null, "meta": {...}, "errors": [{code, message}]}` | Frontend must be updated |
| SSE stream | `event: status\ndata: ...\n\n` (stub) | Structured token stream with `[DONE]` sentinel | New behavior |

> [!IMPORTANT]
> The frontend (Next.js 15) must be updated **in the same sprint** as Phase 4 (envelope standardization). Coordinate with the frontend team before deploying Phase 4 to production.

---

## 4. Migration Strategy

### 4.1 Core Principles

```
NEVER:                              ALWAYS:
- Rewrite working endpoints         - Extract first, refactor second
- Create long-lived branches        - Commit after every task
- Break existing API contracts      - Add, then migrate, then delete
- Stop development for migration    - Keep main deployable at all times
- Mix infrastructure + feature work - One concern per phase
```

### 4.2 Branch Strategy

Use **trunk-based development** with short-lived feature branches per phase:

```
main (always deployable)
  └── feat/phase-01-core-infrastructure  (max 3 days)
  └── feat/phase-02-config-layer          (max 2 days)
  └── feat/phase-03-di-refactor           (max 3 days)
  ...
```

Each phase branch is merged to `main` via PR with mandatory:
- All existing tests passing
- Smoke test of `/health` endpoint
- No imports broken

### 4.3 Migration Pattern

For every component migration, follow this sequence:

```
1. CREATE the new target file (empty implementation)
2. COPY logic from old location → new location
3. UPDATE imports in ONE file at a time
4. ADD tests for the new component
5. VERIFY all existing tests still pass
6. DELETE old file only after all imports point to new location
```

---

## 5. Architecture Dependency Graph

### 5.1 Target Dependency Diagram (Acyclic)

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 0 — Foundation (no dependencies on app code)                │
│                                                                     │
│  core/config.py    core/logging.py    core/exceptions.py           │
│  core/http.py      core/lifespan.py   core/middleware.py           │
│  core/security.py  core/telemetry.py                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ depended on by all layers below
┌──────────────────────────────▼──────────────────────────────────────┐
│  LAYER 1 — Domain Models (no I/O, no DB, no HTTP)                  │
│                                                                     │
│  domain/company/models.py      domain/market/models.py             │
│  domain/analysis/models.py     domain/macro/models.py              │
│  domain/auth/models.py                                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  LAYER 2 — Provider Layer (uses core/http.py + domain models)      │
│                                                                     │
│  providers/supabase/client.py     providers/supabase/executor.py   │
│  providers/capital_stake/client.py   providers/capital_stake/mapper │
│  providers/psx_proxy/client.py    providers/psx_proxy/mapper.py    │
│  providers/fmp/client.py          providers/fmp/mapper.py          │
│  providers/ai/openai_client.py    providers/ai/schemas.py          │
└─────────────┬──────────────────────────┬───────────────────────────┘
              │                          │
┌─────────────▼──────────┐  ┌───────────▼────────────────────────────┐
│  LAYER 3A — Repositories│  │  LAYER 3B — AI Module                  │
│  (Supabase only)        │  │  (providers/ai + domain models)        │
│                         │  │                                        │
│  repositories/base.py   │  │  ai/prompt_builder.py                  │
│  repositories/          │  │  ai/prompt_templates/                  │
│    analysis_repository  │  │  ai/streaming.py                       │
│    macro_repository     │  │  ai/parser.py                          │
│    profile_repository   │  │  ai/validator.py                       │
│                         │  │  ai/cache.py                           │
│                         │  │  ai/analysis_pipeline.py               │
└─────────────┬──────────┘  └───────────┬────────────────────────────┘
              │                          │
┌─────────────▼──────────────────────────▼───────────────────────────┐
│  LAYER 4 — Service Layer (orchestration only — no SQL, no HTTP)    │
│                                                                     │
│  services/company_service.py      services/analysis_service.py     │
│  services/market_service.py       services/macro_service.py        │
│  services/cache_service.py                                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  LAYER 5 — Auth (uses core/security.py + providers/supabase)       │
│                                                                     │
│  auth/jwt.py    auth/dependencies.py    auth/supabase_auth.py      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  LAYER 6 — API Layer (FastAPI routers + DI + schemas)              │
│                                                                     │
│  api/v1/schemas/envelope.py   api/v1/schemas/common.py             │
│  api/v1/dependencies.py       api/v1/router.py                     │
│  api/v1/endpoints/*.py                                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  LAYER 7 — Cross-Cutting (depends on observability + core)         │
│                                                                     │
│  middleware/request_id.py  middleware/timing.py                    │
│  observability/context.py  observability/metrics.py                │
│  observability/tracing.py  tasks/*.py                               │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Critical Dependency Rules (Enforced by Architecture)

| Rule | Enforcement |
|---|---|
| Routers never import `repositories` | Service layer is mandatory intermediary |
| Services never import `httpx` | Providers are mandatory intermediary |
| Repositories never import `services` | Strictly unidirectional |
| Providers never import `repositories` | No cross-layer contamination |
| Domain models have no external imports | Pure Python only |
| `core/` has no imports from `app/` | Zero upward dependencies |

---

## 6. Phase-by-Phase Implementation Plan

---

### Phase 0 — Architecture Audit & Baseline

**Why now?** Must be complete before any code changes. Establishes the baseline.  
**Why not later?** Cannot plan migrations without knowing what exists.

#### Objective
Produce a complete, verified understanding of the current system and establish test coverage that can serve as a regression safety net for all subsequent phases.

#### Files Affected
- `tests/test_main.py` — extend
- `tests/test_auth.py` — extend
- `tests/test_config.py` — extend
- `conftest.py` — update

#### Prerequisites
- None (this is the first phase)

#### Deliverables
- This implementation plan document
- Verified passing test suite as baseline
- Confirmed working `/health` endpoint
- Confirmed working Supabase connection in development

#### Implementation Tasks
- [x] Audit all source files (complete — this document)
- [ ] Run existing test suite: `pytest tests/ -v` — confirm green baseline
- [ ] Document any failing tests before migration begins
- [ ] Confirm `uvicorn app.main:app` starts without errors
- [ ] Write smoke test script verifying all 10 endpoint routes return non-500 in dev mode

#### Validation
```bash
pytest tests/ -v
uvicorn app.main:app --reload
curl http://localhost:8000/health
```

#### Completion Criteria
- All existing tests pass
- Application starts cleanly
- All 10 endpoint routes exist and respond (even with stub/503 responses)

---

### Phase 1 — Core Infrastructure Consolidation

**Why now?** The entire stack depends on `core/`. It must be rock-solid before anything else changes. Fixing it first means every subsequent phase builds on a clean foundation.  
**Why not later?** Moving config after providers or repositories are built causes cascading import re-fixes.

#### Objective
Consolidate `app/config/` and `app/core/` into a single, well-organized `app/core/` package. Add missing exception types. Prepare middleware infrastructure.

#### Files Affected

**New files:**
- `app/core/config.py` — consolidation of `app/config/settings.py`
- `app/core/security.py` — bcrypt helpers extracted from `app/auth.py`
- `app/core/middleware.py` — CORS, request ID, timing (stubs)
- `app/core/lifespan.py` — extracted from `main.py`

**Modified files:**
- `app/core/exceptions.py` — add `AIProviderError`, `RateLimitError`; fix `DatabaseError` status code to 503
- `app/core/logging_config.py` → renamed `app/core/logging.py` — add request_id context filter
- `app/core/__init__.py` — update re-exports
- `app/main.py` — import from new locations; move lifespan out

**Deprecated (kept for 2 phases, then deleted):**
- `app/config/` directory — all imports updated to `app/core/config`

#### Prerequisites
- Phase 0 complete

#### Deliverables
After this phase:
- `app/core/config.py` is the authoritative settings module
- `app/core/logging.py` has enhanced structured logging
- `app/core/exceptions.py` has complete hierarchy
- `app/core/lifespan.py` manages startup/shutdown
- All imports in the codebase point to new `core/` locations
- Application still starts and all tests pass

#### Implementation Tasks
1. **Create `app/core/config.py`** — copy `app/config/settings.py`, add missing settings fields:
   - `CAPITAL_STAKE_BASE_URL: Optional[str]`
   - `PSX_PROXY_BASE_URL: Optional[str]` (rename from `PSX_PROXY_URL`)
   - `AI_MODEL: str = "gpt-4o"`
   - `AI_MAX_TOKENS: int = 4096`
   - `ANALYSIS_CACHE_TTL_HOURS: int = 24`
   - `MACRO_CACHE_TTL_HOURS: int = 6`
   - `DEFAULT_TIMEOUT_SECONDS: float = 10.0`
   - `DEFAULT_MAX_RETRIES: int = 3`
   - `ALLOWED_ORIGINS: list[str]` (rename from `CORS_ORIGINS`)
   - `APP_ENV: str` alias for `ENVIRONMENT`
   - Add `is_production` property
2. **Add compatibility shim** in `app/config/__init__.py` — re-export from `app/core/config` for one phase
3. **Rename `app/core/logging_config.py` → `app/core/logging.py`** using `git mv`
4. **Extend logging** — add `RequestIdFilter` that injects `request_id` from `contextvars` into every log record
5. **Add missing exceptions** — `AIProviderError(status_code=502)`, `RateLimitError(status_code=429)`
6. **Extract lifespan** — move `@asynccontextmanager async def lifespan` from `main.py` to `app/core/lifespan.py`; import back in `main.py`
7. **Create `app/core/security.py`** — move bcrypt `pwd_context` and `hash_password`/`verify_password` from `auth.py`
8. **Update `app/core/__init__.py`** — re-export all public symbols
9. **Update `app/main.py`** — import lifespan from `core/lifespan.py`
10. **Run full test suite** — confirm green

#### Risks
- Import cycle if `core/` accidentally imports from `app/`
- `PSX_PROXY_URL` rename breaks `.env` files that use the old name

#### Mitigation
- Add `PSX_PROXY_URL` as an alias property in settings (read both env vars)
- Use mypy in CI to catch circular imports

#### Validation
```bash
pytest tests/ -v
python -c "from app.core.config import get_settings; print(get_settings())"
python -c "from app.core.exceptions import AIProviderError, RateLimitError; print('OK')"
uvicorn app.main:app
```

#### Rollback Strategy
- All old files remain until explicitly deleted; revert imports to old locations

#### Completion Criteria
- `from app.core.config import get_settings` works
- `from app.core.logging import get_logger` works
- `from app.core.exceptions import AIProviderError` works
- All tests pass

---

### Phase 2 — Dependency Injection & Middleware Infrastructure

**Why now?** Every subsequent phase (repositories, providers, services) will add FastAPI `Depends` functions. The DI infrastructure must be clean before those dependencies are created.  
**Why not later?** Building providers and repositories before DI is clean means retrofitting DI patterns into every file.

#### Objective
Clean up `app/dependencies.py`, add structured middleware (request ID, timing), and standardize how settings and DB are injected.

#### Files Affected

**New files:**
- `app/middleware/request_id.py` — injects `X-Request-ID` header
- `app/middleware/timing.py` — injects `X-Process-Time` header
- `app/middleware/__init__.py`

**Modified files:**
- `app/main.py` — register new middleware; fix per-request Supabase client creation
- `app/dependencies.py` — remove inline `create_client()`; fix per-request client anti-pattern (temporarily)

#### Prerequisites
- Phase 1 complete

#### Deliverables
- Every response has `X-Request-ID` header
- Every response has `X-Process-Time` header
- Request ID available via `contextvars` for log injection
- `get_settings()` remains the DI standard; no imperative calls in endpoints

#### Implementation Tasks
1. **Create `app/middleware/request_id.py`** — `RequestIDMiddleware(BaseHTTPMiddleware)`:
   - Generate `uuid4()` if `X-Request-ID` not in request headers
   - Store in `ContextVar`
   - Inject into response headers
2. **Create `app/middleware/timing.py`** — `TimingMiddleware(BaseHTTPMiddleware)`:
   - Record `time.perf_counter()` at request start
   - Add `X-Process-Time` to response headers in milliseconds
3. **Register middleware in `app/main.py`** (order matters — add AFTER CORS):
   ```python
   app.add_middleware(TimingMiddleware)
   app.add_middleware(RequestIDMiddleware)
   ```
4. **Fix per-request Supabase client** in `app/dependencies.py`:
   - Replace inline `create_client()` with call to the singleton from `app/database/connection.py`
   - Pass JWT via `db.postgrest.auth(token)` on the shared client (thread-safe for this use case)
5. **Write tests** for middleware headers:
   - `test_request_id_header_present`
   - `test_process_time_header_present`
   - `test_request_id_propagated_in_logs`

#### Risks
- Middleware ordering errors causing 500s
- Thread-safety issue with setting auth token on shared Supabase client

#### Mitigation
- Add middleware in correct LIFO order (FastAPI adds in reverse)
- For Supabase client auth token: create a lightweight wrapper that sets the token on the shared client per-call (the `postgrest-py` library is not truly async-safe here; document this as a known temporary limitation until Phase 4 introduces the proper provider)

#### Validation
```bash
curl -v http://localhost:8000/health | grep X-Request-ID
curl -v http://localhost:8000/health | grep X-Process-Time
pytest tests/ -v
```

#### Completion Criteria
- All responses have both headers
- Request ID accessible from `contextvars` in logger

---

### Phase 3 — Auth Module Extraction

**Why now?** `app/auth.py` is a God file. It needs to be split before the repository and service layers are added — those layers will need clean auth dependencies.  
**Why not later?** Splitting auth after services are built means updating auth imports across many more files.

#### Objective
Split `app/auth.py` into a proper `app/auth/` package: `jwt.py`, `dependencies.py`, `supabase_auth.py`.

#### Files Affected

**New files:**
- `app/auth/__init__.py`
- `app/auth/jwt.py` — `AuthService` class (token creation, verification)
- `app/auth/dependencies.py` — `get_current_user`, `get_current_supabase_user` FastAPI Depends
- `app/auth/supabase_auth.py` — Supabase JWT validation logic

**Modified files:**
- Every endpoint file that imports from `app.auth` — update to `app.auth.dependencies`
- `app/main.py` — nothing changes (doesn't import auth)
- `app/dependencies.py` — update import of `security` to `app.auth.dependencies`

**Deprecated:**
- `app/auth.py` — kept as re-export shim for 2 phases, then deleted

#### Prerequisites
- Phase 2 complete

#### Deliverables
- `app/auth/` package with 3 focused modules
- All endpoint imports updated
- `app/auth.py` shim in place for backward compat
- Zero behavior change

#### Implementation Tasks
1. **Create `app/auth/jwt.py`** — move `AuthService` class + `pwd_context` (or import from `core/security.py`) + `security` HTTPBearer
2. **Create `app/auth/supabase_auth.py`** — move `get_current_supabase_user` logic with settings now injected via parameter, not called directly
3. **Create `app/auth/dependencies.py`** — export `get_current_user`, `get_current_supabase_user` as FastAPI Depends functions; import `AuthService` from `jwt.py`
4. **Create `app/auth/__init__.py`** — re-export public symbols
5. **Update `app/auth.py`** — replace all content with re-exports from new package (backward compat shim)
6. **Update imports in all 10 endpoint files** — change `from app.auth import get_current_supabase_user` → `from app.auth.dependencies import get_current_supabase_user`
7. **Write unit tests** for `AuthService`:
   - `test_create_access_token`
   - `test_verify_token_valid`
   - `test_verify_token_invalid`
   - `test_verify_token_expired`
8. **Write unit tests** for Supabase auth:
   - `test_missing_jwt_secret_dev_bypass`
   - `test_missing_bearer_token`
   - `test_invalid_token`

#### Risks
- Import errors if one endpoint file is missed
- `security` HTTPBearer object must be accessible from `dependencies.py`

#### Mitigation
- Use `grep -r "from app.auth"` to find all import sites before starting
- Use `git grep` after changes to verify no stale imports

#### Validation
```bash
python -c "from app.auth.dependencies import get_current_supabase_user; print('OK')"
python -c "from app.auth.jwt import AuthService; print('OK')"
pytest tests/ -v
```

#### Completion Criteria
- `app/auth/` package has 3 modules + `__init__.py`
- All endpoint files import from `app.auth.dependencies`
- All tests pass

---

### Phase 4 — Response Envelope Standardization

**Why now?** The response envelope is the public API contract. Standardizing it now — before services and AI pipeline are built — means those components always emit the correct format. Doing it later would require touching every endpoint twice.  
**Why not later?** The existing `ApiResponse` lacks `meta` (request_id, latency, cache_hit) which the AI pipeline requires for SSE metadata.

> [!IMPORTANT]
> This phase changes the API response format. **Coordinate with the frontend team.** Deploy to staging and validate with the frontend before merging to production.

#### Objective
Create the `APIResponse[T]` generic envelope, migrate all endpoints to use it, and update error responses to the standard format.

#### Files Affected

**New files:**
- `app/api/v1/schemas/__init__.py`
- `app/api/v1/schemas/envelope.py` — `APIResponse[T]`, `Meta`, `ErrorDetail`
- `app/api/v1/schemas/common.py` — `Pagination`, `SortOrder`, `FilterParams`

**Modified files:**
- All 10 endpoint files — update `response_model` and return statements
- `app/main.py` — update exception handlers to return `APIResponse` format
- `app/api/v1/schemas_walltrade.py` — remove `ApiResponse`, keep domain DTOs
- `app/api/v1/router.py` — no change

**Deprecated:**
- `ApiResponse` class in `schemas_walltrade.py` — replaced by `api/v1/schemas/envelope.py`

#### Prerequisites
- Phase 3 complete
- Frontend team notified

#### Deliverables
All API responses in format:
```json
{
  "success": true,
  "data": {...},
  "meta": {"request_id": "uuid", "latency_ms": 12.5, "cache_hit": false},
  "errors": []
}
```

#### Implementation Tasks
1. **Create `app/api/v1/schemas/envelope.py`**:
   - `Meta(BaseModel)` with `request_id: str`, `latency_ms: float`, `cache_hit: bool = False`
   - `ErrorDetail(BaseModel)` with `code: str`, `message: str`
   - `APIResponse(BaseModel, Generic[T])` with `success`, `data`, `meta`, `errors`
   - `def make_response(data: T, request_id: str, start_time: float, cache_hit: bool = False) -> APIResponse[T]` helper
2. **Create `app/api/v1/schemas/common.py`** — `PaginationParams`, `SortOrder` enum
3. **Update `app/main.py` exception handlers** — return `APIResponse` format with `errors` list
4. **Update all 10 endpoints** — replace `ApiResponse(message=..., data=...)` with `APIResponse[T]`; populate `meta` from request context
5. **Update `app/api/v1/schemas_walltrade.py`** — remove `ApiResponse` and `ServiceUnavailableResponse`; keep only DTO classes
6. **Write API tests** for envelope structure:
   - `test_response_has_meta_field`
   - `test_response_has_request_id`
   - `test_error_response_has_errors_list`

#### Risks
- Frontend breaking if deployed without coordination
- `ServiceUnavailableResponse` still used in `analysis.py` and `companies.py` — must be replaced simultaneously

#### Mitigation
- Deploy to staging only; coordinate with frontend before production deployment
- Use feature flag or API version header if needed to support both formats temporarily

#### Validation
```bash
curl http://localhost:8000/health | jq '.meta'
curl http://localhost:8000/api/v1/macro | jq '.meta.request_id'
pytest tests/api/ -v
```

#### Completion Criteria
- All endpoints return `APIResponse[T]`
- `meta.request_id` present on every response
- Exception handlers return `errors` list format

---

### Phase 5 — Provider Layer: Supabase

**Why now?** The Supabase client is the dependency of the Repository Layer (Phase 6). Wrapping it properly in a provider first ensures repositories get a clean, typed client — not a raw singleton.  
**Why not later?** Repositories would be built on top of the current fragile double-singleton pattern.

#### Objective
Wrap the Supabase client in a proper provider package with async-safe lifecycle management.

#### Files Affected

**New files:**
- `app/providers/__init__.py`
- `app/providers/supabase/__init__.py`
- `app/providers/supabase/client.py` — singleton lifecycle, async-safe
- `app/providers/supabase/executor.py` — query execution + APIError → AppException mapping

**Modified files:**
- `app/core/lifespan.py` — initialize Supabase client on startup
- `app/dependencies.py` — use `providers/supabase/client.py` instead of `database/connection.py`

**Deprecated (for removal in Phase 15):**
- `app/database/connection.py`
- `app/database/` directory

#### Prerequisites
- Phase 4 complete

#### Deliverables
- `providers/supabase/client.py` with proper singleton and lifecycle
- `providers/supabase/executor.py` with `_execute()` promoted from `SupabaseDBService`
- All DB access routes through the new provider
- Old `DatabaseManager` kept but no longer the primary path

#### Implementation Tasks
1. **Create `app/providers/supabase/client.py`**:
   - `SupabaseClient` class wrapping `supabase.create_client`
   - `get_supabase_client() -> Client` — singleton factory
   - `get_authed_client(jwt_token: str) -> Client` — creates scoped client with auth token for RLS
   - Initialized in `lifespan.py` on startup
2. **Create `app/providers/supabase/executor.py`**:
   - Promote `_execute` from `SupabaseDBService` to standalone function
   - Add typed error codes and better exception messages
   - Add logging of query details (table, operation) for observability
3. **Update `app/dependencies.py`**:
   - `get_db_dependency` → uses `providers.supabase.client.get_authed_client()`
4. **Update `app/core/lifespan.py`** — call `get_supabase_client()` on startup to fail fast if misconfigured
5. **Write provider tests**:
   - `tests/providers/test_supabase_client.py` — mock Supabase `create_client`
   - Test `get_authed_client` sets the auth token correctly

#### Risks
- Thread-safety of setting auth header on shared client
- Supabase `postgrest-py` sync vs async mismatch

#### Mitigation
- Document the sync limitation explicitly; note that `supabase-py` v2 uses sync PostgREST by default
- Consider wrapping DB calls with `asyncio.run_in_executor()` if latency becomes an issue (defer to performance phase)

#### Completion Criteria
- `from app.providers.supabase.client import get_supabase_client` works
- All endpoint DB calls use the new provider
- All tests pass

---

### Phase 6 — Repository Layer

**Why now?** Repositories are the missing abstraction between `SupabaseDBService` (which exists) and the services layer (which doesn't yet). Building repos before services ensures services never touch DB directly.  
**Why not later?** Without repos, the service layer would have to call `SupabaseDBService` — maintaining the same coupling.

#### Objective
Extract domain-specific repository classes from `SupabaseDBService`. Create a `BaseRepository` with generic CRUD. Replace all direct `SupabaseDBService` calls in routers with the new typed repositories.

#### Files Affected

**New files:**
- `app/repositories/__init__.py`
- `app/repositories/base.py` — `BaseRepository(db_client)` with generic CRUD + `_execute`
- `app/repositories/analysis_repository.py` — `get_valid_cache`, `upsert_cache`, typed returns
- `app/repositories/macro_repository.py` — `get_latest`, typed return
- `app/repositories/profile_repository.py` — `get_by_user_id`, `upsert`
- `app/repositories/portfolio_repository.py` — CRUD for `user_portfolio`
- `app/repositories/trade_repository.py` — CRUD for `user_trades`
- `app/repositories/market_feel_repository.py` — CRUD for `market_feel`
- `app/repositories/sector_feel_repository.py` — CRUD for `sector_feel`
- `app/repositories/script_history_repository.py` — CRUD for `script_history`

**Modified files:**
- `app/api/v1/dependencies.py` (NEW file replacing `app/dependencies.py`) — add `get_analysis_repo`, `get_macro_repo`, etc.
- All 10 endpoint files — replace `SupabaseDBService(db).method()` with repo Depends

**Note:** Endpoints still call repositories directly at this phase. Services will mediate in Phase 8. This is an incremental improvement — routers still call repos but no longer use the generic `SupabaseDBService` with magic string table names.

#### Prerequisites
- Phase 5 complete

#### Deliverables
- All 9 domain repository classes
- `BaseRepository` with `_execute` (moved from `executor.py`)
- All routers use typed repositories instead of `SupabaseDBService`
- `SupabaseDBService` kept as fallback until Phase 15

#### Implementation Tasks
1. **Create `app/repositories/base.py`**:
   ```python
   class BaseRepository:
       def __init__(self, db_client): self.db = db_client
       def _execute(self, query): ...  # from supabase/executor.py
       async def list(self, filters, order_by, limit, offset): ...
       async def get_by_id(self, id): ...
       async def create(self, payload): ...
       async def update(self, id, payload): ...
   ```
2. **Create `app/repositories/analysis_repository.py`**:
   - `get_valid_cache(ticker: str) -> Optional[dict]` — port from `SupabaseDBService.get_analysis_cache`
   - `upsert_cache(payload: dict) -> dict` — port from `SupabaseDBService.upsert_analysis_cache`
3. **Create `app/repositories/macro_repository.py`**:
   - `get_latest() -> Optional[dict]` — port from `SupabaseDBService.get_latest_macro`
4. **Create remaining repositories** (portfolio, trade, market_feel, sector_feel, script_history) using `BaseRepository.list`, `create`, `update`
5. **Create `app/api/v1/dependencies.py`** (new file, different from `app/dependencies.py`):
   - `get_analysis_repo(db=Depends(get_db_dependency)) -> AnalysisRepository`
   - `get_macro_repo(db=Depends(get_db_dependency)) -> MacroRepository`
   - etc.
6. **Update endpoint files** to use repository Depends instead of `SupabaseDBService`
7. **Write integration tests** (mock DB client):
   - `test_analysis_repository_get_valid_cache`
   - `test_analysis_repository_upsert`
   - `test_macro_repository_get_latest`

#### Risks
- Return type is still `dict[str, Any]` — no domain models yet (Phase 7 adds those)
- `SupabaseDBService` still in codebase — risk of new code using old path

#### Mitigation
- Add deprecation warning to `SupabaseDBService.__init__`
- Add linting rule (or code review guideline) prohibiting new imports of `SupabaseDBService`

#### Completion Criteria
- `SupabaseDBService` has zero callers in endpoint files
- All 9 repositories exist and are covered by tests
- All endpoint tests pass

---

### Phase 7 — Domain Models

**Why now?** Services (Phase 8) and AI module (Phase 9) need typed domain models as their communication language. Without domain models, services would deal in raw `dict[str, Any]` — defeating the purpose of a service layer.  
**Why not later?** Cannot build the AI pipeline without `AnalysisResult`, `MacroIndicator`, etc.

#### Objective
Create pure Python domain models for all business concepts. These models have no DB coupling and no HTTP coupling — they are the vocabulary of the application.

#### Files Affected

**New files:**
- `app/domain/__init__.py`
- `app/domain/company/models.py` — `CompanyProfile`, `CompanyMetrics`
- `app/domain/company/enums.py` — `Sector`, `Exchange`
- `app/domain/market/models.py` — `Price`, `OHLCV`, `MarketSentiment`
- `app/domain/market/enums.py` — `MarketDirection`
- `app/domain/analysis/models.py` — `AnalysisResult`, `AnalysisCache`
- `app/domain/analysis/enums.py` — `Sentiment`, `ConfidenceLevel`
- `app/domain/macro/models.py` — `MacroIndicator`, `MacroCache`
- `app/domain/macro/enums.py`
- `app/domain/auth/models.py` — `User`, `Session`
- `app/domain/auth/enums.py`

**Modified files:**
- `app/repositories/analysis_repository.py` — update return types to `Optional[AnalysisCache]`
- `app/repositories/macro_repository.py` — update return type to `Optional[MacroCache]`

#### Prerequisites
- Phase 6 complete

#### Deliverables
- All domain model files with Pydantic v2 models
- Repositories updated to return domain models (not raw dicts)
- Unit tests for all domain models

#### Implementation Tasks
1. **Create domain models** for each subdomain:
   - Use `pydantic.BaseModel` with `model_config = ConfigDict(frozen=True)` where immutability is appropriate
   - Use `datetime` with timezone awareness (`datetime.now(timezone.utc)`)
   - Add `to_dict()` / `from_db_row(row: dict)` classmethods where needed
2. **Update `AnalysisRepository`** — map `dict` → `AnalysisCache` domain model on return
3. **Update `MacroRepository`** — map `dict` → `MacroCache` domain model on return
4. **Write unit tests** — validate all domain models serialize/deserialize correctly

#### Key Domain Models

```python
# domain/analysis/models.py
class AnalysisResult(BaseModel):
    ticker: str
    summary: str
    sentiment: Sentiment
    verdict: str
    key_risks: list[str]
    key_opportunities: list[str]
    generated_at: datetime
    expires_at: datetime
    model_used: str

class AnalysisCache(BaseModel):
    id: int
    ticker: str
    result: AnalysisResult
    created_at: datetime
```

#### Risks
- Repository changes could break endpoint behavior if mapping is incorrect

#### Mitigation
- Add mapper unit tests before updating repositories
- Keep old `dict` return as fallback with compatibility shim

#### Completion Criteria
- All domain models created and unit tested
- Repositories return typed domain models
- All endpoint tests still pass

---

### Phase 8 — Service Layer

**Why now?** Services orchestrate business logic that currently lives inside routers. Extracting this now — after repos (Phase 6) and domain models (Phase 7) are ready — means services can be built correctly on their first creation.  
**Why not later?** The AI pipeline (Phase 9) depends on `AnalysisService`. It cannot be built before the service layer.

#### Objective
Create the service layer that mediates between routers (which currently call repos directly) and the underlying data/AI systems. Update all routers to call services instead of repositories.

#### Files Affected

**New files:**
- `app/services/__init__.py`
- `app/services/analysis_service.py`
- `app/services/company_service.py`
- `app/services/market_service.py`
- `app/services/macro_service.py`
- `app/services/cache_service.py`
- `app/services/portfolio_service.py`
- `app/services/trade_service.py`

**Modified files:**
- `app/api/v1/dependencies.py` — add service factory Depends functions
- All 10 endpoint files — replace repo Depends with service Depends

**Deprecated:**
- `app/services/base_service.py` — replaced by DI
- `app/services/capital_stake.py` — moved to providers in Phase 9
- `app/services/psx_service.py` — moved to providers in Phase 9
- `app/services/supabase_db.py` — superseded by repositories

#### Prerequisites
- Phase 7 complete

#### Deliverables
- Service classes with constructor injection
- Service factory functions in `api/v1/dependencies.py`
- Routers call only services (not repos directly)
- Cache service wraps TTL logic from `supabase_db.py`

#### Implementation Tasks
1. **Create `app/services/cache_service.py`**:
   - `CacheService(analysis_repo: AnalysisRepository)`
   - `get_analysis(ticker: str) -> Optional[AnalysisCache]` — checks TTL, returns None on miss
   - `set_analysis(result: AnalysisResult) -> AnalysisCache`
   - TTL driven by `settings.ANALYSIS_CACHE_TTL_HOURS`
2. **Create `app/services/macro_service.py`**:
   - `MacroService(macro_repo: MacroRepository)`
   - `get_latest() -> Optional[MacroCache]`
3. **Create `app/services/portfolio_service.py`** — thin wrapper over `PortfolioRepository`
4. **Create `app/services/trade_service.py`** — thin wrapper over `TradeRepository`
5. **Create `app/services/analysis_service.py`** (STUB for now — AI pipeline wired in Phase 9):
   - Constructor: `(analysis_repo, cache_service)` — no pipeline yet
   - `get_cached_analysis(ticker) -> Optional[AnalysisCache]` — calls cache service
   - `stream_analysis(ticker) -> AsyncIterator[str]` — returns stub SSE until Phase 9
6. **Create `app/services/company_service.py`** (STUB — Capital Stake wired in Phase 9):
   - `get_company_profile(ticker: str) -> CompanyProfile` — returns NotImplemented stub
7. **Create `app/services/market_service.py`** (STUB — PSX Proxy wired in Phase 9):
   - `get_all_prices() -> list[Price]`
   - `get_price(ticker: str) -> Price`
8. **Add service factory Depends** in `app/api/v1/dependencies.py`:
   ```python
   def get_analysis_service(db=Depends(get_db_dependency)) -> AnalysisService:
       repo = AnalysisRepository(db)
       cache = CacheService(repo)
       return AnalysisService(repo, cache)
   ```
9. **Update all endpoint files** to inject services
10. **Write service unit tests**:
    - Mock repos; test cache hit/miss logic
    - Test TTL expiry logic in CacheService

#### Risks
- Analysis service stub may break the SSE streaming behavior in the analysis endpoint

#### Mitigation
- Preserve existing stub SSE behavior in `AnalysisService.stream_analysis` until Phase 9
- Don't change SSE endpoint behavior — only change where the stub lives

#### Completion Criteria
- No endpoint file imports from `repositories/` directly
- All services constructor-injected via `Depends`
- All tests pass

---

### Phase 9 — Provider Layer: External APIs

**Why now?** Providers depend on `core/http.py` (new) and return domain models (Phase 7). The service layer (Phase 8) is the only consumer of providers. Building providers after services ensures the correct direction of dependency.  
**Why not later?** The AI pipeline (Phase 10) needs the `OpenAIClient` provider.

#### Objective
Build the centralized HTTP client and all external API provider packages. Wire providers into services.

#### Files Affected

**New files:**
- `app/core/http.py` — `AsyncHTTPClient` with retries, timeouts, tracing
- `app/providers/capital_stake/__init__.py`
- `app/providers/capital_stake/client.py`
- `app/providers/capital_stake/mapper.py`
- `app/providers/capital_stake/schemas.py`
- `app/providers/psx_proxy/__init__.py`
- `app/providers/psx_proxy/client.py`
- `app/providers/psx_proxy/mapper.py`
- `app/providers/psx_proxy/schemas.py`
- `app/providers/fmp/__init__.py`
- `app/providers/fmp/client.py`
- `app/providers/fmp/mapper.py`
- `app/providers/fmp/schemas.py`
- `app/providers/ai/__init__.py`
- `app/providers/ai/openai_client.py`
- `app/providers/ai/schemas.py`
- `app/providers/ai/base.py` — `AIProvider(Protocol)`

**Modified files:**
- `app/services/company_service.py` — wire `CapitalStakeClient`
- `app/services/market_service.py` — wire `PSXProxyClient`
- `app/services/macro_service.py` — wire `FMPClient`
- `app/api/v1/dependencies.py` — add provider factory Depends
- `app/core/lifespan.py` — initialize HTTP clients on startup
- `requirements.txt` — add `tenacity`, `httpx` (already present)

#### Prerequisites
- Phase 8 complete
- Capital Stake API documentation available
- PSX Proxy API documentation available

#### Deliverables
- `AsyncHTTPClient` with configurable retries (tenacity), timeouts, circuit breaker stub
- Working `CapitalStakeClient` that returns `CompanyProfile` domain model
- Working `PSXProxyClient` that returns `list[Price]` domain model
- Working `FMPClient` for macro data (if FMP credentials available)
- `AIProvider` Protocol with `OpenAIClient` implementation
- Provider mock tests using `httpx.MockTransport`

#### Implementation Tasks
1. **Create `app/core/http.py`**:
   - `class AsyncHTTPClient`:
     - `__init__(base_url: str, timeout: float, retries: int, api_key: Optional[str])`
     - `async def get(path: str, **params) -> dict`
     - `async def post(path: str, body: dict) -> dict`
     - Uses `httpx.AsyncClient` with `AsyncLimits` for connection pool
     - Uses `tenacity.retry` with `wait_exponential` for retries
     - Logs every outbound request with timing
     - Injects `X-Request-ID` header from current context
   - Lifecycle: `AsyncHTTPClient.aclose()` called in `lifespan` shutdown
2. **Create `app/providers/capital_stake/client.py`**:
   - `CapitalStakeClient(http: AsyncHTTPClient)`
   - `async def get_company_profile(ticker: str) -> CompanyProfile`
   - `async def get_financial_data(ticker: str) -> dict` (for AI pipeline)
3. **Create `app/providers/capital_stake/mapper.py`**:
   - `CompanyMapper.to_domain(raw: dict) -> CompanyProfile`
4. **Create `app/providers/psx_proxy/client.py`**:
   - `PSXProxyClient(http: AsyncHTTPClient)`
   - `async def get_all_prices() -> list[Price]`
   - `async def get_price(ticker: str) -> Price`
5. **Create `app/providers/fmp/client.py`** — FMP macro indicators
6. **Create `app/providers/ai/base.py`** — `AIProvider` Protocol
7. **Create `app/providers/ai/openai_client.py`**:
   - `OpenAIClient(http: AsyncHTTPClient)` or use `openai` library directly
   - `async def stream(prompt: str) -> AsyncIterator[str]`
   - Implements `AIProvider` Protocol
8. **Update `app/api/v1/dependencies.py`** — add provider factory functions
9. **Update `app/services/company_service.py`** — inject `CapitalStakeClient`
10. **Update `app/services/market_service.py`** — inject `PSXProxyClient`
11. **Write provider tests** using `httpx.MockTransport`:
    - `test_capital_stake_get_company_profile`
    - `test_psx_proxy_get_all_prices`
    - `test_openai_stream_returns_tokens`
12. **Update `requirements.txt`** — add `tenacity`, `openai`

#### Risks
- Capital Stake and PSX Proxy API documentation may not be fully available
- OpenAI API key required for real streaming tests

#### Mitigation
- Build against documented API spec first; add retry logic for rate limits
- Use `httpx.MockTransport` for all provider tests — no real API calls in tests
- Add `AI_API_KEY` guard (already exists in settings) to return 503 when absent

#### Completion Criteria
- All provider tests pass with mocked HTTP
- Company and prices endpoints return real data (not stubs) when API keys are configured
- `AsyncHTTPClient` used by all providers

---

### Phase 10 — AI Module & Analysis Pipeline

**Why now?** This is the most complex phase. It must come after providers (Phase 9) because the pipeline depends on `CapitalStakeClient`, `MacroRepository`, and `OpenAIClient`. It must come after domain models (Phase 7) because `PromptBuilder` operates on domain models.  
**Why not later?** The AI analysis is the core product value. This phase is the reason the entire migration exists.

#### Objective
Build the complete AI analysis pipeline as a dedicated module. Wire it into `AnalysisService`. Replace the current stub SSE stream with real token-by-token streaming.

#### Files Affected

**New files:**
- `app/ai/__init__.py`
- `app/ai/prompt_builder.py` — assembles prompts from `AnalysisResult` + `MacroCache`
- `app/ai/prompt_templates/__init__.py`
- `app/ai/prompt_templates/full_analysis.py` — Jinja2/f-string full analysis template
- `app/ai/prompt_templates/quick_summary.py`
- `app/ai/streaming.py` — `StreamManager` — formats raw tokens as SSE
- `app/ai/parser.py` — `AnalysisParser` — raw AI text → `AnalysisResult`
- `app/ai/validator.py` — `AnalysisValidator` — validates parsed result
- `app/ai/cache.py` — `AICache` — wraps `CacheService` for AI-specific logic
- `app/ai/analysis_pipeline.py` — `AnalysisPipeline` — orchestrates all steps

**Modified files:**
- `app/services/analysis_service.py` — inject `AnalysisPipeline`; implement real streaming
- `app/api/v1/dependencies.py` — add `get_analysis_pipeline` factory
- `app/api/v1/endpoints/analysis.py` — update streaming endpoint
- `requirements.txt` — add `openai`, `jinja2`

#### Prerequisites
- Phase 9 complete
- OpenAI API key available (or Gemini as alternative)
- Capital Stake API available for financial data fetch

#### Deliverables
- Full AI analysis pipeline that:
  1. Checks cache
  2. Fetches company financials via `CapitalStakeClient`
  3. Fetches macro data via `MacroRepository`
  4. Builds structured prompt via `PromptBuilder`
  5. Streams tokens from OpenAI via `OpenAIClient`
  6. Formats as SSE via `StreamManager`
  7. Parses and validates result
  8. Persists to `analysis_cache` via `AnalysisRepository`
- Real SSE streaming to browser

#### Implementation Tasks
1. **Create `app/ai/prompt_builder.py`**:
   - `PromptBuilder.build(company_data: dict, macro_data: MacroCache, ticker: str) -> str`
   - Accept domain models, not raw dicts
2. **Create `app/ai/prompt_templates/full_analysis.py`** — Jinja2 template or f-string builder
3. **Create `app/ai/streaming.py`**:
   - `StreamManager.format_sse(token: str) -> str` — formats as `data: {...}\n\n`
   - `StreamManager.done_event() -> str` — emits `data: [DONE]\n\n`
4. **Create `app/ai/parser.py`**:
   - `AnalysisParser.parse(raw_text: str) -> AnalysisResult`
   - Handles partial/malformed AI output gracefully
5. **Create `app/ai/validator.py`** — Pydantic-based validation of parsed result
6. **Create `app/ai/analysis_pipeline.py`**:
   ```python
   class AnalysisPipeline:
       def __init__(
           self,
           capital_stake: CapitalStakeClient,
           macro_repo: MacroRepository,
           prompt_builder: PromptBuilder,
           ai_provider: AIProvider,
           cache: CacheService,
           analysis_repo: AnalysisRepository,
       ): ...

       async def run(self, ticker: str) -> AsyncIterator[str]:
           # 1. Cache check (delegate to AnalysisService)
           # 2. Fetch financials
           # 3. Fetch macro
           # 4. Build prompt
           # 5. Stream AI
           # 6. Format SSE
           # 7. Parse + validate
           # 8. Save to cache
           yield ...
   ```
7. **Update `AnalysisService`** — inject `AnalysisPipeline`; `stream_analysis` delegates to pipeline
8. **Update `analysis.py` endpoint** — remove stub SSE; delegate fully to service
9. **Write unit tests**:
   - `test_prompt_builder_builds_structured_prompt`
   - `test_stream_manager_formats_sse`
   - `test_analysis_parser_extracts_verdict`
   - `test_analysis_validator_rejects_invalid`
10. **Write pipeline integration test** (mocked providers):
    - `test_pipeline_returns_cached_on_hit`
    - `test_pipeline_streams_tokens_on_miss`

#### Risks
- OpenAI API unavailability during development
- Malformed AI output breaking parser
- SSE stream disconnection mid-stream

#### Mitigation
- Use `MockAIProvider` in all tests
- Parser must be defensive — return partial result on parse failure, not exception
- Add error SSE event on exception: `event: error\ndata: {...}\n\n`

#### Completion Criteria
- Real SSE streaming from AI to browser
- Cache hit returns cached result without calling AI
- Pipeline unit tests at >90% coverage

---

### Phase 11 — Observability

**Why now?** With the AI pipeline live (Phase 10), we need production-grade observability to debug AI latency, cache performance, and external API health.  
**Why not later?** Operating an AI streaming service in production without metrics is a significant operational risk.

#### Objective
Add `RequestContext` propagation, Prometheus metrics, and structured observability hooks throughout the stack.

#### Files Affected

**New files:**
- `app/observability/__init__.py`
- `app/observability/context.py` — `RequestContext` dataclass + `ContextVar`
- `app/observability/metrics.py` — Prometheus counters and histograms
- `app/observability/tracing.py` — OpenTelemetry span helpers (stub initially)

**Modified files:**
- `app/middleware/request_id.py` — set `RequestContext` in context var
- `app/middleware/timing.py` — record latency into context
- `app/core/http.py` — record external API latency into context
- `app/ai/analysis_pipeline.py` — record AI latency into context
- `app/services/cache_service.py` — set `cache_hit` in context
- `app/api/v1/schemas/envelope.py` — populate `meta` from context (not function args)
- `app/main.py` — add `/metrics` endpoint
- `requirements.txt` — add `prometheus_client`, `opentelemetry-sdk`

#### Prerequisites
- Phase 10 complete

#### Deliverables
- `RequestContext` propagated through every request
- `meta.request_id`, `meta.latency_ms`, `meta.cache_hit` populated from context automatically
- `/metrics` endpoint exposing Prometheus metrics
- All 5 metrics defined in `ARCHITECTURE.md` implemented

#### Implementation Tasks
1. **Create `app/observability/context.py`** — full `RequestContext` dataclass with `ContextVar`
2. **Update `app/middleware/request_id.py`** — call `set_ctx(RequestContext(...))` per request
3. **Create `app/observability/metrics.py`**:
   - `request_total` Counter
   - `request_latency_ms` Histogram
   - `cache_hit_total` Counter
   - `ai_latency_ms` Histogram
   - `external_api_latency_ms` Histogram (labeled by provider)
4. **Update `app/core/http.py`** — record provider name + latency into `RequestContext`
5. **Update `app/ai/analysis_pipeline.py`** — record AI call latency
6. **Update `app/api/v1/schemas/envelope.py`** — `make_response()` reads from `get_ctx()`
7. **Add `/metrics` endpoint** to `main.py` (unauthenticated — for Prometheus scraping)
8. **Create stub `app/observability/tracing.py`** — OTEL integration (can be expanded later)

#### Risks
- `ContextVar` not propagated across `asyncio.create_task` boundaries

#### Mitigation
- Use `contextvars.copy_context().run()` for background tasks spawned during requests

#### Completion Criteria
- `curl http://localhost:8000/metrics` returns Prometheus text format
- All requests have `meta.request_id` in response
- `meta.cache_hit: true` when analysis served from cache

---

### Phase 12 — Background Tasks

**Why now?** Background tasks (macro refresh, cache cleanup) were identified as missing but non-critical. With observability in place, task health can be monitored.  
**Why not later?** Without cache refresh tasks, macro data becomes stale; without cleanup tasks, `analysis_cache` will grow unbounded.

#### Objective
Implement APScheduler-based background tasks for cache management and health monitoring.

#### Files Affected

**New files:**
- `app/tasks/__init__.py`
- `app/tasks/refresh_macro.py`
- `app/tasks/cleanup_cache.py`
- `app/tasks/warm_cache.py`
- `app/tasks/health_checks.py`

**Modified files:**
- `app/core/lifespan.py` — register all tasks with APScheduler
- `requirements.txt` — add `apscheduler`

#### Prerequisites
- Phase 11 complete

#### Deliverables
- APScheduler running inside FastAPI lifespan
- 4 background tasks registered and running

#### Implementation Tasks
1. **Add `apscheduler` to `requirements.txt`**
2. **Create task functions** in each `tasks/` file
3. **Update `app/core/lifespan.py`**:
   ```python
   scheduler.add_job(refresh_macro, "interval", hours=6)
   scheduler.add_job(cleanup_cache, "cron", hour=0)
   scheduler.add_job(warm_cache, "interval", hours=12)
   scheduler.add_job(health_checks, "interval", minutes=5)
   scheduler.start()
   ```
4. **Write task smoke tests** — verify tasks are registered (not that they run end-to-end)

#### Completion Criteria
- Scheduler starts with app
- Tasks execute on schedule without errors

---

### Phase 13 — Testing Infrastructure

**Why now?** With the full stack implemented, a proper test suite is now achievable. Tests written earlier were unit tests. This phase builds the full pyramid.  
**Why not later?** Without integration and API tests, confident deployment to production is impossible.

#### Objective
Build the complete testing pyramid: unit, integration, API, provider, and performance baseline.

#### Files Affected

**New files:**
- `tests/conftest.py` — shared fixtures: test app factory, mock DB, mock HTTP transport
- `tests/factories/` — `AnalysisResultFactory`, `MacroFactory`, etc.
- `tests/fixtures/` — static JSON payloads for Capital Stake, PSX, OpenAI
- `tests/unit/` — all pure logic tests
- `tests/integration/` — Supabase integration tests
- `tests/api/` — FastAPI TestClient end-to-end tests
- `tests/providers/` — HTTP mock transport tests

**Modified files:**
- `pyproject.toml` — add test dependencies

#### Prerequisites
- Phase 12 complete (full stack exists)

#### Deliverables
- Full test pyramid covering all phases
- `pytest tests/ --cov` achieving >70% overall coverage
- CI pipeline running all test tiers

#### Implementation Tasks
1. **Create `tests/conftest.py`** with:
   - `test_app` fixture using `create_app()` with overridden dependencies
   - Mock DB client fixture
   - Mock HTTP transport fixture
2. **Create model factories** using `pytest` fixtures (or `factory_boy`)
3. **Create static fixture files** in `tests/fixtures/` for all external APIs
4. **Write unit tests**:
   - `test_prompt_builder.py`
   - `test_analysis_parser.py`
   - `test_analysis_validator.py`
   - `test_cache_service.py`
5. **Write integration tests** (real Supabase test project):
   - `test_analysis_repository.py`
   - `test_macro_repository.py`
6. **Write API tests** (TestClient):
   - `test_analysis_endpoint.py` — SSE streaming, cache hit, 503 when keys missing
   - `test_companies_endpoint.py`
   - `test_health_endpoint.py`
7. **Write provider tests** (httpx MockTransport):
   - `test_capital_stake_client.py`
   - `test_psx_proxy_client.py`

#### Completion Criteria
- `pytest tests/unit/` — 100% pass, <5s
- `pytest tests/api/` — 100% pass
- `pytest tests/ --cov` — >70% coverage
- Zero `xfail` tests

---

### Phase 14 — Performance Optimizations

**Why now?** With tests in place (Phase 13), performance regressions can be detected. Without tests, optimization is blind.  
**Why not later?** SSE streaming with AI latency and Supabase latency stacked requires early optimization.

#### Objective
Profile and optimize critical paths: Supabase latency, HTTP client connection pooling, async correctness.

#### Files Affected
- `app/core/http.py` — tune connection pool limits
- `app/utils/decorators.py` — replace homegrown retry with tenacity
- `app/repositories/base.py` — review sync/async boundary
- `app/providers/supabase/client.py` — review async safety
- `app/api/v1/endpoints/analysis.py` — validate streaming backpressure

#### Prerequisites
- Phase 13 complete

#### Deliverables
- Connection pool correctly configured for expected concurrency
- `tenacity` integrated into `AsyncHTTPClient` retries
- No blocking I/O on the async event loop
- Performance baseline documented in `tests/performance/`

#### Implementation Tasks
1. **Profile baseline** using `locust` or `wrk`: measure `/api/v1/macro` and `/api/v1/analyse/{ticker}` latencies
2. **Review Supabase client** for blocking sync calls — wrap in `asyncio.run_in_executor` if needed
3. **Tune `AsyncHTTPClient`** connection pool: `limits=httpx.Limits(max_connections=50, max_keepalive_connections=20)`
4. **Replace `utils/decorators.py` retry logic** with `tenacity` integration
5. **Document performance baseline** in `tests/performance/README.md`

#### Completion Criteria
- Macro endpoint P95 latency < 200ms
- Analysis cache hit P95 latency < 100ms
- Analysis cache miss + AI P95 latency < 5000ms (AI-bound)

---

### Phase 15 — Cleanup & Technical Debt Removal

**Why now?** Only after all phases are complete and tested can dead code be safely deleted.  
**Why not later?** Dead code accumulates confusion and maintenance burden.

#### Objective
Delete all deprecated files, shims, and orphaned code. Finalize documentation.

#### Files to Delete
- `app/auth.py` (shim — replaced by `app/auth/` package)
- `app/config/` directory (replaced by `app/core/config.py`)
- `app/database/` directory (replaced by `app/providers/supabase/`)
- `app/routes/` directory (orphaned — never registered)
- `app/models/schemas.py` (replaced by `app/domain/` models)
- `app/utils/responses.py` (replaced by `app/api/v1/schemas/`)
- `app/services/base_service.py` (replaced by DI)
- `app/services/capital_stake.py` (replaced by provider)
- `app/services/psx_service.py` (replaced by provider)
- `app/services/supabase_db.py` (replaced by repositories)
- `app/api/v1/schemas.py` (empty stub)
- `app/database.py` (1-line stub)

**Updated files:**
- `README.md` — update with new architecture
- `CONTRIBUTING.md` — update with new patterns
- `API_STRUCTURE.md` — update with final endpoint map
- `requirements.txt` — remove unused packages

#### Prerequisites
- Phase 14 complete
- All tests passing with no imports from deprecated files

#### Validation
```bash
grep -r "from app.auth import" app/   # should return nothing
grep -r "from app.config import" app/ # should return nothing
grep -r "from app.database import" app/ # should return nothing
grep -r "SupabaseDBService" app/      # should return nothing
pytest tests/ --cov
```

#### Completion Criteria
- Zero imports from deleted files
- All tests pass
- `git log --stat` shows only deletions in this phase

---

## 7. Risk Register

| ID | Risk | Probability | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | Frontend breaks on envelope format change (Phase 4) | High | High | Stage-gate deployment; coordinate with frontend team | Backend + Frontend |
| R-02 | Supabase sync/async mismatch causes event loop blocking | Medium | High | Profile early; wrap in executor if needed | Backend |
| R-03 | Capital Stake API undocumented behavior | Medium | Medium | Build with defensive mapper; add integration tests | Backend |
| R-04 | OpenAI rate limits during AI pipeline development | High | Medium | Use mock provider in tests; implement retry with backoff | Backend |
| R-05 | `contextvars` not propagated through `asyncio.create_task` | Medium | Medium | Use `copy_context().run()` in task spawning | Backend |
| R-06 | Long-lived SSE connection exhausts connection pool | Low | High | Limit concurrent streams; add backpressure | Backend |
| R-07 | APScheduler task fails silently | Medium | Medium | Add Prometheus counter for task success/failure | Backend |
| R-08 | Breaking import change missed during refactor | Medium | High | Use `grep`/mypy before every PR merge | Backend |
| R-09 | Supabase RLS blocks service-role queries after refactor | Low | High | Test RLS behavior in dev with both anon and service keys | Backend |
| R-10 | Phase dependencies violated (building out of order) | Low | High | This plan is the enforced sequence; no skipping phases | Architect |

---

## 8. Testing Strategy

### Test Pyramid

```
                ┌───────────────────┐
                │   E2E / Manual    │  (staging + postman)
                ├───────────────────┤
                │    API Tests      │  (FastAPI TestClient)
                ├───────────────────┤
                │ Provider Tests    │  (httpx MockTransport)
                ├───────────────────┤
                │ Integration Tests │  (real Supabase test project)
                ├───────────────────┤
                │   Unit Tests      │  (no I/O, <5s total)
                └───────────────────┘
```

### Per-Phase Test Requirements

| Phase | Test Type | Command | Success Metric |
|---|---|---|---|
| 0 | Smoke | `pytest tests/ -v` | All existing pass |
| 1 | Unit | `pytest tests/unit/test_core.py` | 100% pass |
| 2 | API | `pytest tests/api/test_middleware.py` | Headers present |
| 3 | Unit | `pytest tests/unit/test_auth.py` | 100% pass |
| 4 | API | `pytest tests/api/` | Envelope structure correct |
| 5 | Provider | `pytest tests/providers/test_supabase.py` | Client mocked |
| 6 | Integration | `pytest tests/integration/` | Repos return typed models |
| 7 | Unit | `pytest tests/unit/test_domain.py` | All models serialize |
| 8 | Unit | `pytest tests/unit/test_services.py` | Cache hit/miss logic |
| 9 | Provider | `pytest tests/providers/` | All providers mocked |
| 10 | Unit + API | `pytest tests/unit/test_ai.py tests/api/test_analysis.py` | SSE streaming works |
| 11 | API | Metrics endpoint test | Prometheus format valid |
| 12 | Smoke | Task registration test | Scheduler starts |
| 13 | Full suite | `pytest tests/ --cov` | >70% coverage |
| 14 | Perf | `locust` or `wrk` | P95 targets met |
| 15 | Regression | `pytest tests/ --cov` | No coverage drop |

### Manual Verification Checklist (Per Phase)

- [ ] Application starts without errors
- [ ] `/health` returns 200
- [ ] `/api/v1/macro` returns valid data
- [ ] `/api/v1/analyse/{ticker}` returns SSE stream (Phase 10+)
- [ ] Swagger UI (`/docs`) loads all endpoints
- [ ] No 500 errors in logs

---

## 9. Rollback Strategy

### Global Rollback Principle
Every phase branch is merged via PR only after tests pass. The `main` branch is always deployable. To roll back any phase:

```bash
git revert HEAD~N   # revert N commits (keep history)
# OR
git reset --hard <last-good-commit>  # destructive — only if not deployed
```

### Per-Phase Rollback

| Phase | Rollback Method | Risk of Rollback |
|---|---|---|
| 1 (Core) | Keep shim in `app/config/` — old imports still work for 2 phases | None |
| 2 (Middleware) | Remove middleware registrations from `main.py` | None |
| 3 (Auth) | `app/auth.py` shim re-exports from new package — revert shim to original | Low |
| 4 (Envelope) | Highest risk — requires frontend coordination | High — coordinate rollback with frontend |
| 5 (Supabase Provider) | Old `DatabaseManager` kept — revert `dependencies.py` | Low |
| 6 (Repositories) | Old `SupabaseDBService` kept — revert endpoint imports | Medium |
| 7–15 | New files only — delete new files to roll back | Low |

### Deployment Rollback (Production)
- Each phase is deployed independently to staging before production
- Staging smoke tests must pass before production deploy
- Use blue-green or canary deployment if available

---

## 10. Technical Debt Register

| ID | Debt Item | Location | Severity | Resolution Phase |
|---|---|---|---|---|
| TD-01 | Blocking Supabase sync calls on async event loop | `database/connection.py`, `supabase_db.py` | High | Phase 5 (wrap) / Phase 14 (optimize) |
| TD-02 | `create_client()` called per-request in `dependencies.py` | `app/dependencies.py:44` | High | Phase 5 |
| TD-03 | God file auth module | `app/auth.py` | High | Phase 3 |
| TD-04 | Business logic in routers | All CRUD endpoints | High | Phase 8 |
| TD-05 | Magic string table names in endpoints | `portfolios.py`, `trades.py`, etc. | Medium | Phase 6 |
| TD-06 | Non-generic response envelope | `schemas_walltrade.ApiResponse` | Medium | Phase 4 |
| TD-07 | No request ID in logs | `core/logging_config.py` | Medium | Phase 1 |
| TD-08 | Orphaned code (`routes/`, `models/`, `responses.py`) | Various | Low | Phase 15 |
| TD-09 | Inline imports inside functions (`decorators.py`) | `utils/decorators.py` | Low | Phase 14 |
| TD-10 | `python-jose` + `passlib` both in requirements | `requirements.txt` | Low | Phase 3 (consolidate to `PyJWT` + `bcrypt`) |
| TD-11 | Dual singleton pattern in `database/connection.py` | `database/connection.py` | Medium | Phase 5 |
| TD-12 | No `OPENAI_API_KEY` in settings (uses `AI_API_KEY`) | `config/settings.py` | Low | Phase 1 |
| TD-13 | TTL hardcoded as 24 hours in `supabase_db.py` | `supabase_db.py:111` | Low | Phase 6 (driven by settings) |
| TD-14 | `sqlalchemy` logger configured but SQLAlchemy not used | `core/logging_config.py` | Low | Phase 15 |

---

## 11. Future Expansion Opportunities

Once the target architecture is in place, the following expansions become low-risk due to proper layer isolation:

| Opportunity | Prerequisite Phase | Effort | Impact |
|---|---|---|---|
| **Redis cache layer** | Phase 6 | Low — swap `CacheService` backend | High — sub-millisecond cache |
| **Gemini/Anthropic provider** | Phase 9 | Low — implement `AIProvider` Protocol | High — AI provider flexibility |
| **Celery for heavy background tasks** | Phase 12 | Medium — replace APScheduler | High — distributed task processing |
| **Redis Streams event bus** | Phase 8 | Medium — add `EventBus` after services | High — NotificationService, AuditService |
| **Microservices extraction** | Phase 8 | High — extract domain by domain | Strategic — split Analysis into own service |
| **Mobile client support** | Phase 4 | Low — envelope already standardized | High — no API contract changes needed |
| **Multi-tenancy** | Phase 6 | Medium — add `tenant_id` to repositories | High — SaaS model |
| **Rate limiting** | Phase 2 | Low — add `slowapi` middleware | Medium — API protection |
| **WebSocket alternative to SSE** | Phase 10 | Medium — add WS endpoint alongside SSE | Medium — bidirectional AI interaction |
| **OpenTelemetry full tracing** | Phase 11 | Medium — expand tracing.py stub | High — distributed tracing to Grafana |
| **FMP macro data refresh** | Phase 12 | Low — implement `refresh_macro` task | High — always-fresh macro cache |

---

## 12. Final Migration Checklist

### Pre-Migration
- [ ] All team members have read this plan
- [ ] Staging environment is configured
- [ ] Frontend team is notified about Phase 4 (envelope change)
- [ ] Capital Stake API documentation is available
- [ ] PSX Proxy API documentation is available
- [ ] OpenAI API key is available for Phase 9+
- [ ] Supabase test project is available for integration tests

### Phase Completion Gates (must pass before next phase)
- [ ] Phase 0 — Baseline tests pass, app starts
- [ ] Phase 1 — `from app.core.config import get_settings` works; all tests pass
- [ ] Phase 2 — All responses have `X-Request-ID`; all tests pass
- [ ] Phase 3 — `app/auth/` package works; all endpoints import from new package
- [ ] Phase 4 — All responses return `APIResponse[T]`; frontend validated on staging
- [ ] Phase 5 — Supabase client in provider; no per-request `create_client()`
- [ ] Phase 6 — Zero `SupabaseDBService` calls in endpoints; typed repos exist
- [ ] Phase 7 — All domain models created; repositories return typed models
- [ ] Phase 8 — Zero repo imports in endpoints; services constructor-injected
- [ ] Phase 9 — All providers tested with mocks; `AsyncHTTPClient` in use
- [ ] Phase 10 — Real SSE streaming works; AI pipeline unit tested
- [ ] Phase 11 — `/metrics` endpoint live; `meta` populated from context
- [ ] Phase 12 — APScheduler starts; 4 tasks registered
- [ ] Phase 13 — >70% test coverage; full pyramid green
- [ ] Phase 14 — Performance baselines documented and met
- [ ] Phase 15 — Zero imports from deprecated files; dead code deleted

### Post-Migration
- [ ] `ARCHITECTURE.md` reflects final implemented state
- [ ] `README.md` updated with new developer setup instructions
- [ ] `CONTRIBUTING.md` updated with new architecture patterns
- [ ] Monitoring dashboard configured (Grafana + Prometheus)
- [ ] All team members trained on new architecture patterns
- [ ] Runbook created for production operations

---

*Document generated by architectural audit of the WallTrade Backend codebase. All decisions are justified and ordered. The implementing engineer should not need to make architectural decisions — only execute this plan.*
