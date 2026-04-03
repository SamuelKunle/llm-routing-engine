## 🚀 Overview

This project demonstrates a production-inspired architecture for building scalable AI-powered applications using modern full-stack technologies.

Designed with a focus on:
- clean system architecture
- scalability and extensibility
- real-world product workflows
- AI integration patterns

This is not just a demo — it reflects how real systems are structured and evolved.

# LLM routing engine

This is a small FastAPI service I built to show how I think about backend structure when multiple LLM providers are in play. You send a chat-style request, the app picks a provider (or falls through to the next one if something breaks), and you always get back the same JSON shape no matter who answered.

I kept the footprint small on purpose: it should be easy to read in one sitting, but the layout is what I would reach for on a real team—clear boundaries, typed requests, and tests that actually assert behavior instead of just importing modules.

If you are here from a job posting or a mutual contact: clone it, run it with the mock provider (no keys required), skim `docs/architecture.md` if you want the tour, and poke the `/docs` UI locally. That is the fastest way to see what is going on.

Source on GitHub: [github.com/SamuelKunle/llm-routing-engine](https://github.com/SamuelKunle/llm-routing-engine)

---

## What you get

**HTTP surface**

- `GET /health` — liveness-style check plus which provider names the router knows about.
- `POST /chat` — validated body, routed generation, normalized response.

**Behavior**

- Pluggable providers: OpenAI-compatible chat completions, Anthropic Messages API, and a local mock that never calls the network.
- Configurable default provider and fallback order via environment variables.
- When fallback is enabled, failures that surface as `ProviderError` trigger the next provider in order; the response tells you whether a fallback happened and which providers were tried.
- Request timeouts on outbound HTTP calls; misconfigured providers (e.g. missing API key) fail fast with a clear error type.

**Non-goals**

This is not a full API gateway. There is no streaming, no per-user auth, no billing, and no distributed rate limiting. Those are listed under [Possible next steps](#possible-next-steps) so the scope stays honest.

---

## Stack

Python 3, FastAPI, Pydantic v2 / pydantic-settings, httpx for async HTTP, pytest for tests. Uvicorn to run the app.

---

## Repository layout

```text
llm-routing-engine/
├── app/
│   ├── main.py                 # App factory, logging, router mount
│   ├── api/chat.py             # /health and /chat routes
│   ├── core/                   # Settings, logging
│   ├── schemas/chat.py         # Request/response and internal result types
│   ├── services/
│   │   ├── router.py           # Ordering, fallback loop, calls normalizer
│   │   ├── normalizer.py       # ProviderResult → public ChatResponse
│   │   └── providers/          # One module per backend
│   └── utils/errors.py
├── docs/architecture.md        # Deeper design notes
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

---

## Quick start

**1. Virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

**2. Dependencies**

```bash
pip install -r requirements.txt
```

**3. Environment**

```bash
cp .env.example .env
```

Edit `.env` if you want real providers; the mock works with no keys.

**4. Run**

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Interactive OpenAPI: `http://127.0.0.1:8000/docs`

---

## Configuration

All settings load from the environment (and optionally `.env`). These are the ones that matter day to day:

| Variable | Role |
|----------|------|
| `APP_NAME` | Title exposed in FastAPI metadata. |
| `DEBUG` | Passed through settings for future use; logging is INFO by default. |
| `REQUEST_TIMEOUT_SECONDS` | httpx client timeout for provider HTTP calls. |
| `DEFAULT_PROVIDER` | Used when the client omits `preferred_provider`. |
| `FALLBACK_PROVIDERS` | Comma-separated list defining order after the first attempt when `allow_fallback` is true. Unknown names are skipped. |
| `OPENAI_*` | API key, base URL, and model for the OpenAI adapter (`/v1/chat/completions`). |
| `ANTHROPIC_*` | API key, base URL, and model for Anthropic (`/v1/messages`, `anthropic-version: 2023-06-01`). |

Copy from `.env.example` and fill in keys only for providers you intend to call. Keep `.env` out of version control.

---

## API reference

### `GET /health`

Returns JSON like:

```json
{
  "status": "ok",
  "available_providers": ["openai", "anthropic", "mock"]
}
```

### `POST /chat`

**Body fields**

| Field | Notes |
|-------|--------|
| `message` | Required. User text, 1–8000 characters. |
| `preferred_provider` | Optional. One of `openai`, `anthropic`, `mock`. If omitted, `DEFAULT_PROVIDER` is used. |
| `allow_fallback` | Default `true`. If `false`, only the first provider in the computed order is attempted. |
| `temperature` | `0.0`–`2.0`, default `0.2`. |
| `max_tokens` | `1`–`4000`, default `300`. |

**Successful response**

| Field | Meaning |
|-------|--------|
| `success` | Always `true` on 200. |
| `message` | Assistant text in one string. |
| `provider_used` | Which adapter satisfied the request. |
| `model_used` | Model id or name from settings. |
| `fallback_used` | `true` if the first provider in the attempt list did not win. |
| `metadata` | Includes `latency_ms` and `attempted_providers` (order of tries). |

**Errors**

If every provider in the ordered list throws a `ProviderError`, the API responds with **502** and a string `detail` describing the last failure.

Validation errors (bad JSON, out-of-range numbers) return **422** via FastAPI/Pydantic.

---

## Try it with curl

```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain provider fallback in one sentence.",
    "preferred_provider": "mock",
    "allow_fallback": true
  }' | python -m json.tool
```

Example shape:

```json
{
  "success": true,
  "message": "Mock reply: Explain provider fallback in one sentence.",
  "provider_used": "mock",
  "model_used": "mock-default",
  "fallback_used": false,
  "metadata": {
    "latency_ms": 12,
    "attempted_providers": ["mock"]
  }
}
```

---

## How routing behaves

The router builds an ordered list: start with `preferred_provider` (or the default), then append each name from `FALLBACK_PROVIDERS` that is not already in the list, but only if `allow_fallback` is true. Names that are not registered adapters are dropped.

For each provider in order, it calls `generate()`. On success, the normalizer builds the public `ChatResponse` and attaches whether a fallback was used and the full attempt list. On `ProviderError`, it logs a warning and moves on. If the list is exhausted, it raises—your client sees a 502.

Provider-specific HTTP details (URLs, headers, parsing) live in the adapter modules under `app/services/providers/`.

---

## Tests

From the project root with your venv active:

```bash
pip install -r requirements.txt
pytest tests/ -v
```

There is an API-level test against the mock provider, a health check test, and an async unit test on the router that injects fake failing/succeeding providers to prove the fallback path. I did not add live integration tests that hit OpenAI or Anthropic; those would need secrets and stable network, which is awkward in CI for a demo repo.

---

## Docs

For a step-by-step request path, design tradeoffs, and notes on extending the codebase, see [docs/architecture.md](docs/architecture.md).

---

## Possible next steps

Ideas I would consider if this grew into a product: streaming responses, rate limits, circuit breaking backed by something like Redis, structured metrics, auth and per-tenant config. None of that is required to understand the current design.

---

## License

Add a `LICENSE` file before publishing if you want a standard grant of rights; this README does not substitute for that.
