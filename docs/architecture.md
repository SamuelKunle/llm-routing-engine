# Architecture

This note is for anyone who wants the story behind the folders, not just a file tree. The code is small enough that you can still read it straight through; treat this as a map.

---

## End-to-end path

A client hits `POST /chat`. FastAPI hands the JSON body to Pydantic, which gives us a `ChatRequest` with sane bounds on message length, temperature, and token limits.

The route module keeps a single `LLMRouter` instance. That router owns a dictionary of provider name → adapter instance (`openai`, `anthropic`, `mock`). It does not know HTTP details—it only knows each adapter implements `generate(request) -> ProviderResult`.

The router figures out **which order to try**. First slot is either the client’s `preferred_provider` or `DEFAULT_PROVIDER` from settings. If fallback is allowed, it walks `FALLBACK_PROVIDERS` from the environment (comma-separated) and appends any name that is not already in the list and that exists in the registry. That gives a single ordered list with no duplicates.

Then it loops. On each iteration it records the provider name in `attempted`, calls `generate`, and on success passes the `ProviderResult` plus attempt metadata into the normalizer. The normalizer’s job is tiny but important: it is the only place that turns internal fields into the public `ChatResponse`, so the API contract stays stable if a provider’s raw payload changes.

If `generate` raises `ProviderError`, the router logs and continues. Configuration problems (missing API key) are also `ProviderError` subclasses, so they participate in the same loop—meaning a bad OpenAI key could still fall through to Anthropic or mock depending on your order. That is deliberate for a demo: production systems might treat “not configured” differently from “HTTP 500 from vendor.”

When nothing succeeds, the last error message is raised as `ProviderError` and the route maps that to HTTP 502.

---

## Why separate router, normalizer, and providers

**Router** — orchestration only. No knowledge of OpenAI’s JSON versus Anthropic’s. Easy to unit test by swapping the provider map.

**Normalizer** — one choke point for the outward JSON. If you add fields later (for example trace ids), you touch one function.

**Providers** — each file is a thin adapter: build URL and headers, call httpx, parse success JSON into `ProviderResult`, map transport errors to `ProviderError`. The mock provider skips the network entirely and still returns the same `ProviderResult` type, which keeps the router dumb and happy.

---

## Configuration

`pydantic-settings` loads `.env` and environment variables into a cached `Settings` object. Timeouts and model names live there so adapters do not hardcode vendor defaults in multiple places.

---

## Error model

`ProviderError` is the generic “this attempt failed” type. `ProviderConfigurationError` subclasses it for missing keys. The API layer only catches `ProviderError` for `/chat` and converts to 502; validation stays with FastAPI’s 422 handling.

---

## Testing strategy

Integration-style tests use `TestClient` against the real app and the mock provider—fast, no secrets.

The router test replaces `router.providers` with tiny fake classes that succeed or fail on demand, so we can prove fallback and `attempted_providers` without mocking httpx.

---

## Adding another provider

Practical order of operations:

1. Add a class under `app/services/providers/` that subclasses `BaseProvider`, sets `name`, and implements `async def generate`.
2. Register it in `LLMRouter.__init__` inside `self.providers`.
3. Extend `.env.example` with any new settings; wire them in `app/core/config.py`.
4. Document the new name in the README and add it to `FALLBACK_PROVIDERS` if you want it in the rotation.

Keep returning `ProviderResult` with `latency_ms` filled so metadata stays meaningful.

---

## What this does not try to solve

No connection pooling across requests beyond what httpx does per call, no retries inside a single provider call beyond “try next provider,” no streaming, no prompt templating system, no tool use. Those are product concerns; this repo is a slice through routing and normalization.
