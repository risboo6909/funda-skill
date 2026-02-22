# Funda Gateway Workflow

This file describes how an agent should manage the local Funda gateway safely.

## Rules

- Use the gateway only on `127.0.0.1`
- Do not expose it publicly
- Reuse an existing local `.venv` in the Funda skill folder when possible

## 1. Check if the gateway is already running

Use a quick local check before starting a new process:

```bash
curl -s http://127.0.0.1:9090/search_listings >/dev/null
```

If the command returns HTTP 200 (or valid JSON), reuse the running gateway.

## 2. Prepare Python environment (only if needed)

From the Funda skill local folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r scripts/requirements.txt
```

If `.venv` already exists, only run:

```bash
source .venv/bin/activate
```

## 3. Start the gateway

Start from the Funda skill local folder:

```bash
python scripts/funda_gateway.py --port 9090 --timeout 10
```

Notes:
- The gateway binds to `127.0.0.1` only
- If port `9090` is already in use by the gateway, startup will stop instead of launching another instance

## 4. Health check after start

```bash
curl -sG "http://127.0.0.1:9090/search_listings" \
  --data-urlencode "location=Amsterdam" \
  --data-urlencode "page=0"
```

Expected:
- HTTP 200
- JSON object response (possibly empty)

## 5. Stop the gateway (when needed)

If running in foreground, stop with `Ctrl+C`.

If the process was started in background, find and stop it explicitly:

```bash
lsof -iTCP:9090 -sTCP:LISTEN -n -P
kill <PID>
```

## 6. Troubleshooting

- TLS / CA error (`curl: (77)`):
  - activate `.venv`
  - reinstall requirements: `python -m pip install -r scripts/requirements.txt`
- Port already in use:
  - verify if the gateway is already running and reuse it
  - otherwise stop the process using that port
