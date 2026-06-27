"""Performance baseline documentation."""

# Performance targets (Phase 14):
# - Macro endpoint P95 latency < 200ms
# - Analysis cache hit P95 latency < 100ms
# - Analysis cache miss + AI P95 latency < 5000ms

BASELINE_TARGETS = {
    "macro_p95_ms": 200,
    "analysis_cache_hit_p95_ms": 100,
    "analysis_miss_ai_p95_ms": 5000,
}
