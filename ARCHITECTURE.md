# ARCHITECTURE GUIDE — WallTrade Backend

> **Production-grade FastAPI backend for a fintech AI platform.**
> FastAPI is the correct BFF for this stack (Next.js + Supabase + external financial APIs + AI streaming) because it handles async I/O, SSE `StreamingResponse`, dependency injection, and Pydantic validation natively. All improvements below focus on internal architecture, not the framework.

---

## Architecture Rating

| Version | Score | Notes |
|---|---|---|
| v1 (original) | 7.5 / 10 | Good layered foundation; fine for a CRUD API |
| v2 (this guide) | — | Production-ready fintech AI platform |

---

## System Architecture Overview

```
┌───────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Next.js)                              │
└─────────────────────────────┬─────────────────────────────────────────┘
                              │  HTTP / SSE
┌─────────────────────────────▼─────────────────────────────────────────┐
│                     FASTAPI APPLICATION                               │
│                                                                       │
│  ┌────────────┐   ┌──────────────┐   ┌───────────────────────────┐   │
│  │ Middleware  │   │  API Layer   │   │  Observability / Tracing  │   │
│  │ (CORS,Auth,│   │  v1 Routers  │   │  (Request ID, Metrics,    │   │
│  │  Logging,  │   │  Endpoints   │   │   Latency, Cache Hit)     │   │
│  │  Req ID)   │   │  Schemas/DTO │   └───────────────────────────┘   │
│  └────────────┘   └──────┬───────┘                                   │
│                          │  DI (Depends)                             │
│              ┌───────────▼────────────┐                              │
│              │     SERVICE LAYER      │                              │
│              │  (Business Orchestration)│                            │
│              │  AnalysisService       │                              │
│              │  CompanyService        │                              │
│              │  MarketService         │                              │
│              │  MacroService          │                              │
│              │  CacheService          │                              │
│              └──┬─────────┬───────────┘                             │
│                 │         │                                          │
│     ┌───────────▼──┐  ┌───▼──────────────┐                         │
│     │  AI MODULE   │  │  REPOSITORY LAYER │                         │
│     │  (Pipeline,  │  │  (Data Access)    │                         │
│     │   Streaming, │  │  AnalysisRepo     │                         │
│     │   Prompts,   │  │  MacroRepo        │                         │
│     │   Cache)     │  │  ProfileRepo      │                         │
│     └───────┬───────┘  └───────┬───────────┘                        │
│             │                  │                                     │
│     ┌───────▼──────────────────▼──────────┐                         │
│     │          PROVIDER LAYER             │                         │
│     │  CapitalStakeClient  PSXProxyClient │                         │
│     │  OpenAIClient        SupabaseClient │                         │
│     │  FMPClient                          │                         │
│     └─────────────────────────────────────┘                         │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Target Directory Structure

```
app/
│
├── main.py                          # FastAPI app factory (create_app)
│
├── core/                            # Cross-cutting infrastructure
│   ├── config.py                    # Singleton settings (Pydantic BaseSettings)
│   ├── logging.py                   # Structured JSON logger setup
│   ├── security.py                  # JWT validation, bcrypt, helpers
│   ├── middleware.py                # Request ID injection, timing, CORS
│   ├── exceptions.py                # Exception hierarchy + handlers
│   ├── lifespan.py                  # FastAPI lifespan (startup/shutdown hooks)
│   ├── http.py                      # ⭐ Centralized async HTTP client (retries, timeouts)
│   └── telemetry.py                 # OpenTelemetry / Prometheus metrics setup
│
├── api/
│   └── v1/
│       ├── router.py                # Aggregates all v1 sub-routers
│       ├── dependencies.py          # Shared FastAPI Depends (auth, db, cache)
│       ├── schemas/                 # ⭐ Response envelopes + shared DTOs
│       │   ├── envelope.py          # APIResponse[T], ErrorDetail
│       │   └── common.py            # Pagination, sorting, filters
│       └── endpoints/
│           ├── prices.py
│           ├── companies.py
│           ├── macro.py
│           ├── analysis.py          # ⭐ Streaming analysis endpoint
│           ├── portfolios.py
│           ├── trades.py
│           └── health.py
│
├── domain/                          # ⭐ Domain models (pure Python, no DB coupling)
│   ├── company/
│   │   ├── models.py                # Company, Sector dataclasses / Pydantic models
│   │   └── enums.py
│   ├── market/
│   │   ├── models.py                # Price, OHLCV, MarketFeel
│   │   └── enums.py
│   ├── analysis/
│   │   ├── models.py                # AnalysisResult, AnalysisCache
│   │   └── enums.py
│   ├── macro/
│   │   ├── models.py                # MacroIndicator, MacroCache
│   │   └── enums.py
│   └── auth/
│       ├── models.py                # User, Session
│       └── enums.py
│
├── services/                        # ⭐ Business orchestration (no DB, no HTTP)
│   ├── company_service.py           # Uses CompanyRepo + CapitalStakeClient
│   ├── analysis_service.py          # Uses AnalysisRepo + AI pipeline
│   ├── market_service.py            # Uses PSXClient + MarketRepo
│   ├── macro_service.py             # Uses MacroRepo + FMPClient
│   └── cache_service.py             # Wraps CacheRepository (swap Redis/Supabase)
│
├── repositories/                    # ⭐ Data access (Supabase only, no business logic)
│   ├── base.py                      # BaseRepository with generic CRUD + execute helper
│   ├── analysis_repository.py       # analysis_cache table operations
│   ├── macro_repository.py          # macro_cache table operations
│   └── profile_repository.py        # user profiles table operations
│
├── providers/                       # ⭐ External system clients (isolated, typed)
│   ├── capital_stake/
│   │   ├── client.py                # Async HTTP client using core/http.py
│   │   ├── mapper.py                # Raw JSON → domain models
│   │   └── schemas.py               # Raw response shapes (not exposed to services)
│   ├── psx_proxy/
│   │   ├── client.py
│   │   ├── mapper.py
│   │   └── schemas.py
│   ├── fmp/
│   │   ├── client.py
│   │   ├── mapper.py
│   │   └── schemas.py
│   ├── ai/
│   │   ├── openai_client.py         # Raw OpenAI / Gemini HTTP wrapper
│   │   └── schemas.py
│   └── supabase/
│       ├── client.py                # Supabase connection singleton
│       └── executor.py              # query builder + APIError → AppException
│
├── ai/                              # ⭐ AI is the product — its own subsystem
│   ├── prompt_builder.py            # Assembles prompts from domain models
│   ├── prompt_templates/            # Jinja2 / f-string templates
│   │   ├── full_analysis.py
│   │   └── quick_summary.py
│   ├── streaming.py                 # SSE token-by-token stream manager
│   ├── parser.py                    # Raw AI output → structured AnalysisResult
│   ├── validator.py                 # JSON schema / Pydantic validation of AI output
│   ├── cache.py                     # AI result cache logic (TTL, invalidation)
│   └── analysis_pipeline.py        # ⭐ Orchestrates the full AI analysis flow
│
├── auth/
│   ├── jwt.py                       # Token creation, decoding, expiry
│   ├── dependencies.py              # get_current_user FastAPI dependency
│   └── supabase_auth.py             # Supabase Auth provider wrapper
│
├── middleware/
│   ├── request_id.py                # Injects X-Request-ID on every request
│   ├── timing.py                    # Adds X-Process-Time response header
│   └── auth_middleware.py           # Optional global auth check
│
├── observability/                   # ⭐ Production debugging infrastructure
│   ├── metrics.py                   # Prometheus counters, histograms
│   ├── tracing.py                   # OpenTelemetry span helpers
│   └── context.py                   # RequestContext (request_id, user_id, ticker)
│
├── tasks/                           # ⭐ Background workers (APScheduler / Celery)
│   ├── refresh_macro.py             # Periodically refresh macro cache
│   ├── cleanup_cache.py             # Expire stale analysis cache entries
│   ├── warm_cache.py                # Pre-warm popular tickers
│   └── health_checks.py             # External API reachability checks
│
├── utils/
│   ├── decorators.py                # @retry, @timed, @cached
│   ├── pagination.py                # Cursor / offset pagination helpers
│   └── datetime_utils.py           # Timezone-aware datetime helpers
│
└── tests/                           # ⭐ Multi-tier test architecture
    ├── conftest.py                  # Shared fixtures, test app factory
    ├── factories/                   # Model factories (Factory Boy / pytest fixtures)
    ├── fixtures/                    # Static JSON payloads, mock responses
    ├── unit/                        # Pure logic, no I/O
    │   ├── test_prompt_builder.py
    │   ├── test_parser.py
    │   └── test_cache_service.py
    ├── integration/                 # Real DB / real Supabase (test tenant)
    │   ├── test_analysis_repository.py
    │   └── test_macro_repository.py
    ├── api/                         # FastAPI TestClient end-to-end
    │   ├── test_analysis_endpoint.py
    │   └── test_health_endpoint.py
    └── providers/                   # HTTP mock tests (httpx MockTransport)
        ├── test_capital_stake_client.py
        └── test_psx_proxy_client.py
```

---

## Architecture Layers — Detailed

### Layer 1 — Core Infrastructure (`core/`)

Infrastructure that every other layer depends on. **No business logic allowed here.**

| File | Responsibility |
|---|---|
| `config.py` | Pydantic `BaseSettings` singleton; validated on startup |
| `logging.py` | JSON structured logger factory |
| `security.py` | bcrypt hashing, JWT sign/verify |
| `middleware.py` | CORS, request ID, timing registration |
| `exceptions.py` | Exception hierarchy + FastAPI exception handlers |
| `lifespan.py` | `@asynccontextmanager` startup/shutdown (DB pool, scheduler) |
| `http.py` | **Centralized async HTTP client** — retries, timeouts, circuit breaker, tracing |
| `telemetry.py` | OpenTelemetry tracer/meter setup |

> **Rule:** Every provider uses `core/http.py` — never instantiate `httpx.AsyncClient()` directly inside a provider.

---

### Layer 2 — API Layer (`api/v1/`)

FastAPI routers, endpoints, and schemas. **No business logic. No DB calls.**

```
Router
  │
  ▼  (FastAPI Depends)
Endpoint
  │
  ▼  (injected service)
Service
```

All endpoints return a **response envelope**:

```json
{
  "success": true,
  "data": { ... },
  "meta": { "request_id": "abc-123", "latency_ms": 142, "cache_hit": true },
  "errors": []
}
```

Defined in `api/v1/schemas/envelope.py`:

```python
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")

class Meta(BaseModel):
    request_id: str
    latency_ms: float
    cache_hit: bool = False

class ErrorDetail(BaseModel):
    code: str
    message: str

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    meta: Optional[Meta] = None
    errors: List[ErrorDetail] = []
```

---

### Layer 3 — Domain Models (`domain/`)

Pure Python dataclasses or Pydantic models. **No DB logic. No HTTP logic.** These are the language of the application — all layers communicate using domain models.

```
domain/analysis/models.py

class AnalysisResult(BaseModel):
    ticker: str
    summary: str
    sentiment: Sentiment       # enum
    key_risks: list[str]
    key_opportunities: list[str]
    generated_at: datetime
    expires_at: datetime
    model_used: str
```

---

### Layer 4 — Service Layer (`services/`)

Orchestrates business logic. **No SQL. No raw HTTP calls.**

Services depend on:
- **Repositories** (for persistence)
- **Provider clients** (for external data)
- **AI pipeline** (for AI features)
- **CacheService** (for caching)

```python
class AnalysisService:
    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        cache_service: CacheService,
        pipeline: AnalysisPipeline,
    ): ...

    async def get_analysis(self, ticker: str) -> AsyncIterator[str]:
        # 1. Check cache
        cached = await self.cache_service.get(ticker)
        if cached:
            yield cached.to_sse_json()
            return

        # 2. Run AI pipeline (streams tokens)
        async for chunk in self.pipeline.run(ticker):
            yield chunk
```

---

### Layer 5 — Repository Layer (`repositories/`)

All Supabase (database) access lives here. **No business logic.**

```python
class AnalysisRepository(BaseRepository):
    TABLE = "analysis_cache"

    async def get_valid(self, ticker: str) -> Optional[AnalysisCache]:
        ...

    async def upsert(self, result: AnalysisResult) -> AnalysisCache:
        ...
```

> **Key benefit:** If you migrate from Supabase to raw PostgreSQL or add Redis, only the repositories change. Services are completely untouched.

---

### Layer 6 — Provider Layer (`providers/`)

Thin clients that communicate with external systems. Each provider is fully **isolated** in its own sub-package.

```
providers/capital_stake/
    client.py    ← async HTTP calls using core/http.py
    mapper.py    ← raw JSON dict → domain model
    schemas.py   ← raw response shapes (internal, not exposed upward)
```

```python
class CapitalStakeClient:
    def __init__(self, http: AsyncHTTPClient): ...

    async def get_company_profile(self, ticker: str) -> CompanyProfile:
        raw = await self.http.get(f"/company/{ticker}")
        return CompanyMapper.to_domain(raw)
```

---

### Layer 7 — AI Module (`ai/`)

AI is the core product. It gets its own module instead of being a single growing service file.

#### Analysis Pipeline

```
Ticker
  │
  ▼  cache_service.get(ticker)
Cache Lookup ──────────────────────────────────→ Return cached (SSE)
  │ (miss)
  ▼
Financial Fetch (CapitalStakeClient)
  │
  ▼
Macro Fetch (MacroRepository)
  │
  ▼
Prompt Builder (prompt_builder.py)
  │
  ▼
AI Provider (providers/ai/openai_client.py)
  │
  ▼
SSE Stream Manager (streaming.py) ──────────→ Browser tokens
  │
  ▼
JSON Validator + Parser (validator.py, parser.py)
  │
  ▼
Save to Cache (AnalysisRepository)
  │
  ▼
Return complete AnalysisResult
```

Every step is a replaceable module. Swap OpenAI for Gemini by changing only `providers/ai/`.

---

## Data Flow — Full Request Lifecycle

```
Browser Request
  │
  ▼
Middleware (inject request_id, start timer)
  │
  ▼
Auth Middleware (validate Supabase JWT)
  │
  ▼
FastAPI Router → Endpoint
  │
  ▼  (FastAPI Depends)
Dependencies (get_current_user, get_db, get_analysis_service)
  │
  ▼
AnalysisService.get_analysis(ticker)
  │
  ├─→ CacheService.get(ticker) ──────→ CacheRepository ──→ Supabase
  │         │
  │         ▼ (cache miss)
  │   AnalysisPipeline.run(ticker)
  │         │
  │         ├─→ CapitalStakeClient.get_financials(ticker)
  │         ├─→ MacroRepository.get_latest()
  │         ├─→ PromptBuilder.build(financial_data, macro_data)
  │         ├─→ OpenAIClient.stream(prompt)
  │         └─→ StreamManager.yield_tokens() ──────────────→ SSE Browser
  │
  ▼
Middleware (add X-Process-Time, request_id to response)
  │
  ▼
Observability (record latency, cache_hit, ai_latency metrics)
```

---

## Design Patterns

### 1. Singleton Pattern — Settings
```python
# core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    OPENAI_API_KEY: str
    ...
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 2. Dependency Injection — Services
```python
# api/v1/dependencies.py
def get_analysis_service(
    db = Depends(get_db),
    settings = Depends(get_settings_dep),
) -> AnalysisService:
    repo = AnalysisRepository(db)
    cache = CacheService(repo)
    pipeline = AnalysisPipeline(...)
    return AnalysisService(repo, cache, pipeline)
```

### 3. Repository Pattern
```python
# repositories/base.py
class BaseRepository:
    def __init__(self, db_client): self.db = db_client

    def _execute(self, query): ...   # APIError → AppException

# repositories/analysis_repository.py
class AnalysisRepository(BaseRepository):
    TABLE = "analysis_cache"
    ...
```

### 4. Strategy Pattern — AI Providers
```python
# providers/ai/base.py
class AIProvider(Protocol):
    async def stream(self, prompt: str) -> AsyncIterator[str]: ...

# providers/ai/openai_client.py
class OpenAIProvider:
    async def stream(self, prompt: str) -> AsyncIterator[str]: ...
```

### 5. Pipeline Pattern — Analysis
```python
# ai/analysis_pipeline.py
class AnalysisPipeline:
    steps: list[PipelineStep] = [
        FetchFinancials,
        FetchMacro,
        BuildPrompt,
        StreamAI,
        ParseResult,
        ValidateResult,
        SaveCache,
    ]
    async def run(self, ticker: str) -> AsyncIterator[str]: ...
```

### 6. Factory Pattern — App
```python
# main.py
def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(v1_router, prefix="/api/v1")
    register_middleware(app)
    register_exception_handlers(app)
    return app
```

---

## Observability

Every request carries a `RequestContext` through the entire call stack:

```python
# observability/context.py
from contextvars import ContextVar
from dataclasses import dataclass

@dataclass
class RequestContext:
    request_id: str
    user_id: str | None
    ticker: str | None
    start_time: float
    cache_hit: bool = False
    ai_latency_ms: float | None = None
    external_api_latency_ms: dict[str, float] = field(default_factory=dict)

_ctx: ContextVar[RequestContext] = ContextVar("request_context")

def get_ctx() -> RequestContext: return _ctx.get()
def set_ctx(ctx: RequestContext): _ctx.set(ctx)
```

Metrics exposed at `/metrics` (Prometheus-compatible):

| Metric | Type | Labels |
|---|---|---|
| `walltrade_request_total` | Counter | `endpoint`, `method`, `status` |
| `walltrade_request_latency_ms` | Histogram | `endpoint` |
| `walltrade_cache_hit_total` | Counter | `type` (analysis, macro) |
| `walltrade_ai_latency_ms` | Histogram | `model` |
| `walltrade_external_api_latency_ms` | Histogram | `provider` |

---

## Centralized HTTP Client

**Never** instantiate `httpx.AsyncClient()` directly in a provider. Use `core/http.py`:

```python
# core/http.py
class AsyncHTTPClient:
    """
    Features:
    - configurable retries (tenacity)
    - per-host timeouts
    - circuit breaker (per provider)
    - automatic request ID propagation
    - structured logging of every outbound request
    - latency recording into RequestContext
    """
    def __init__(self, base_url: str, timeout: float = 10.0, retries: int = 3): ...
    async def get(self, path: str, **kwargs) -> dict: ...
    async def post(self, path: str, body: dict, **kwargs) -> dict: ...
```

---

## Streaming / SSE Architecture

Streaming goes through a structured pipeline — **not** directly from routers:

```
Router (StreamingResponse)
  │
  ▼
AnalysisService.stream_analysis(ticker)
  │
  ▼
AnalysisPipeline.run(ticker)
  │
  ▼
OpenAIClient.stream(prompt)   ← raw token stream
  │
  ▼
StreamManager.format_sse(tokens)  ← formats as data: {...}\n\n
  │
  ▼
Browser (EventSource)
```

```python
# api/v1/endpoints/analysis.py
@router.get("/{ticker}/analysis")
async def stream_analysis(
    ticker: str,
    service: AnalysisService = Depends(get_analysis_service),
):
    return StreamingResponse(
        service.stream_analysis(ticker),
        media_type="text/event-stream",
    )
```

---

## Error Handling

```
AppException (base)
├── ValidationError          → 422
├── DatabaseError            → 503
├── AuthenticationError      → 401
├── AuthorizationError       → 403
├── ResourceNotFoundError    → 404
├── ConflictError            → 409
├── ExternalServiceError     → 502
├── AIProviderError          → 502
└── RateLimitError           → 429
```

All errors return the standard envelope:

```json
{
  "success": false,
  "data": null,
  "meta": { "request_id": "abc-123" },
  "errors": [
    { "code": "RESOURCE_NOT_FOUND", "message": "Ticker AAPL not found." }
  ]
}
```

---

## Background Tasks (`tasks/`)

Workers run via APScheduler (or Celery for heavier workloads):

| Task | Schedule | Purpose |
|---|---|---|
| `refresh_macro.py` | Every 6 hours | Keep macro_cache fresh |
| `cleanup_cache.py` | Daily | Remove expired analysis_cache rows |
| `warm_cache.py` | On startup / nightly | Pre-warm top 20 tickers |
| `health_checks.py` | Every 5 min | Alert if external API is unreachable |

Registered in `core/lifespan.py`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(refresh_macro, "interval", hours=6)
    scheduler.start()
    yield
    scheduler.shutdown()
```

---

## Testing Strategy

```
tests/
├── conftest.py              # test app, mock DB, mock HTTP transport
├── factories/               # data factories for domain models
├── fixtures/                # static JSON responses from providers
│
├── unit/                    # no I/O — pure logic
│   ├── test_prompt_builder.py
│   ├── test_parser.py
│   ├── test_validator.py
│   └── test_cache_logic.py
│
├── integration/             # real Supabase (test project/tenant)
│   ├── test_analysis_repository.py
│   └── test_macro_repository.py
│
├── api/                     # FastAPI TestClient (full stack, mocked providers)
│   ├── test_analysis_endpoint.py
│   ├── test_companies_endpoint.py
│   └── test_health_endpoint.py
│
└── providers/               # httpx MockTransport for external APIs
    ├── test_capital_stake_client.py
    └── test_psx_proxy_client.py
```

Run commands:

```bash
pytest tests/unit/          # fast — no I/O
pytest tests/api/           # integration with TestClient
pytest tests/ --cov         # full suite with coverage
pytest -k "analysis"        # filter by keyword
```

---

## Configuration Management

```python
# core/config.py
class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str

    # AI
    OPENAI_API_KEY: str
    AI_MODEL: str = "gpt-4o"
    AI_MAX_TOKENS: int = 4096

    # External APIs
    CAPITAL_STAKE_BASE_URL: str
    PSX_PROXY_BASE_URL: str
    FMP_API_KEY: str

    # Cache
    ANALYSIS_CACHE_TTL_HOURS: int = 24
    MACRO_CACHE_TTL_HOURS: int = 6

    # HTTP Client
    DEFAULT_TIMEOUT_SECONDS: float = 10.0
    DEFAULT_MAX_RETRIES: int = 3

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## Security

| Concern | Approach |
|---|---|
| Authentication | Supabase JWT validation in `auth/dependencies.py` |
| Authorization | Role-based checks in endpoint dependencies |
| Secrets | `pydantic-settings` loads from env; never hardcoded |
| CORS | Configurable allow-list via `Settings.ALLOWED_ORIGINS` |
| Rate Limiting | `slowapi` middleware (per user ID) |
| Error Responses | No stack traces or secrets in responses |
| Input Validation | Pydantic models on all request bodies and query params |

---

## Domain-Driven Grouping (Future Growth)

As each domain grows, its files can be co-located:

```
domain/analysis/
    models.py        ← AnalysisResult, AnalysisCache
    enums.py         ← Sentiment, ConfidenceLevel
    exceptions.py    ← AnalysisNotFoundError, AnalysisExpiredError

services/
    analysis_service.py   ← business orchestration

repositories/
    analysis_repository.py  ← DB access

ai/
    analysis_pipeline.py  ← AI-specific orchestration

api/v1/endpoints/
    analysis.py   ← HTTP layer
```

Everything related to Analysis stays together conceptually, while respecting the layer separation.

---

## Event Layer (Future)

When the platform grows, add an event bus without touching existing services:

```
AnalysisService
  │
  ▼ publish
EventBus ("analysis.generated")
  │
  ├─→ NotificationService  → email / push
  ├─→ AnalyticsService     → usage tracking
  └─→ AuditService         → compliance log
```

Implementation options: Redis Streams, Supabase Realtime, or a lightweight in-process `asyncio.Queue`.

---

## Best Practices Summary

| Category | Status | Standard |
|---|---|---|
| Configuration | ✅ | Pydantic BaseSettings, env-file, validated on startup |
| Dependency Injection | ✅ | FastAPI `Depends`, no manual instantiation in endpoints |
| Error Handling | ✅ | Typed exception hierarchy, standard envelope |
| Logging | ✅ | JSON structured, per-module loggers, no print() |
| Type Hints | ✅ | Full annotations; Pydantic for I/O boundaries |
| Async | ✅ | `async/await` throughout; `asyncio` task management |
| Repository Layer | 🔲 | Isolate all Supabase queries behind repositories |
| Provider Layer | 🔲 | Wrap all external clients in `providers/` sub-packages |
| AI Module | 🔲 | Extract AI pipeline into `ai/` module |
| Response Envelope | 🔲 | Standardize all responses with `APIResponse[T]` |
| Observability | 🔲 | Add `RequestContext`, Prometheus metrics, OTEL tracing |
| Background Tasks | 🔲 | Schedule `tasks/` with APScheduler |
| Cache Abstraction | 🔲 | Route all caching through `CacheService` |
| Testing Tiers | 🔲 | Split tests into unit / integration / api / providers |
| Centralized HTTP | 🔲 | All providers use `core/http.py` |

---

## Development Workflow

```bash
# Setup
make install
cp .env.example .env

# Run dev server
make dev

# Run tests
pytest tests/unit/         # fast feedback
pytest tests/ --cov        # full coverage

# Format & lint
make format
make lint

# Docker
docker-compose up -d
```

---

## Migration Path (Current → Target)

| Priority | Step | Impact |
|---|---|---|
| 1 (now) | Extract `SupabaseDBService` methods into typed `repositories/` | Unblocks all other changes |
| 2 | Move `capital_stake.py` and `psx_service.py` into `providers/` | Isolates external API coupling |
| 3 | Add `core/http.py` centralized client | Enables retries, tracing, circuit breakers |
| 4 | Create `APIResponse[T]` envelope, apply to all endpoints | Consistent frontend contract |
| 5 | Extract `ai/analysis_pipeline.py` from analysis endpoint | Makes AI flow testable and replaceable |
| 6 | Add `observability/context.py` and middleware | Enables production debugging |
| 7 | Add `tasks/` with APScheduler for background jobs | Removes blocking calls from request path |
| 8 | Expand test suite to unit / integration / api / providers | Enables confident refactoring |
