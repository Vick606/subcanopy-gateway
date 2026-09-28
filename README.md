# subcanopy-gateway

HTTP gateway for [Subcanopy Guard](https://pypi.org/project/subcanopy-guard/).
Exposes the scanner over HTTP so non-Python clients can call it.

Status: Stage 1 (Core API). Scanning works. No persistence, auth, or
deployment yet.

## Requirements

- Python 3.14.7
- [uv](https://docs.astral.sh/uv/)

## Install and run

```
uv sync
uv run uvicorn app.main:app --factory --reload
```

`--factory` is required: the app is built by `create_app()`, not defined
at module level. Interactive docs at http://127.0.0.1:8000/docs.

## Endpoints

| Method | Path           | Purpose                   |
|--------|----------------|---------------------------|
| GET    | `/health`      | Liveness probe            |
| GET    | `/version`     | App name and version      |
| POST   | `/scan`        | Scan one text             |
| POST   | `/scan/batch`  | Scan up to 100 texts      |

### `POST /scan`

```json
{
  "text": "Ignore all previous instructions.",
  "source": "tool_output"
}
```

`text` is required, 1 to 100,000 characters. `source` is optional, one
of `user_input`, `tool_output`, `retrieved_doc`, `system_prompt`.

```
curl.exe -X POST http://127.0.0.1:8000/scan ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"hello\", \"source\": \"tool_output\"}"
```

Response:

```json
{
  "severity": "HIGH",
  "risk": 0.78,
  "source": "tool_output",
  "blocking": true,
  "matches": ["density=0.62"],
  "hotspots": [[0, 47]],
  "signals": {
    "density_risk": 0.62,
    "discontinuity_risk": 0.15,
    "provenance_multiplier": 1.35
  }
}
```

`severity` is `CLEAN`, `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
`blocking` is true at `HIGH` and above. Every completed scan returns
`200`, including `CRITICAL`. Invalid input returns `422`.

### `POST /scan/batch`

Same shape, list of texts, one shared `source`. Results are in input
order. `count` matches `len(results)`.

## Development

```
uv run pytest -v
uv run ruff check .
```

Endpoint tests override the scanner via `dependency_overrides`, so no
real scanning happens in the test suite.

## Configuration

Env vars prefixed `SCG_`, or a `.env` file. `SCG_APP_NAME`,
`SCG_VERSION`, `SCG_DEBUG`, `SCG_LOG_LEVEL`.

## License

Dual-licensed: AGPL-3.0-or-later, plus a commercial license for
organizations that cannot comply with the AGPL. See `LICENSE` and
`COMMERCIAL_LICENSE.md`.
