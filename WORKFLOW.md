# Funda Gateway Workflow

Short operating guide for agents managing the local Funda gateway.

## Rules

- Default bind: `127.0.0.1` (loopback)
- Ask the user which interface to use on first startup (`127.0.0.1` or `0.0.0.0`)
- If user does not specify, use `127.0.0.1`
- For periodic tasks in OpenClaw / ClawHub, use **Heartbeat** (not cron)
- Do not rely on `0.0.0.0` for ClawHub cron jobs (cron may run in isolated environment)
- Reuse a healthy running gateway; do not restart on every request
- Restart only after skill update or when unhealthy
- Do not expose the gateway publicly (no auth / no rate limiting)

Heartbeat docs:
- https://docs.openclaw.ai/gateway/heartbeat

## 1. Check Running Gateway

Check process first:

```bash
pgrep -af "python.*scripts/funda_gateway.py"
```

Optional health check:

```bash
curl -s http://127.0.0.1:9090/search_listings >/dev/null
```

If healthy, reuse it.

## 2. Prepare Environment (if needed)

From the Funda skill local folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r scripts/requirements.txt
```

If `.venv` already exists:

```bash
source .venv/bin/activate
```

## 3. Start Gateway

Default (recommended):

```bash
python scripts/funda_gateway.py --host 127.0.0.1 --port 9090 --timeout 10
```

Only if user explicitly wants non-loopback binding:

```bash
python scripts/funda_gateway.py --host 0.0.0.0 --port 9090 --timeout 10
```

Notes:
- Startup stops if the selected `host:port` is already occupied by the gateway
- `127.0.0.1` remains preferred for normal agent usage

## 4. Health Check After Start

```bash
curl -sG "http://127.0.0.1:9090/search_listings" \
  --data-urlencode "location=Amsterdam" \
  --data-urlencode "page=0"
```

Expect HTTP 200 + JSON object (possibly empty).

## 5. Stop Gateway (if needed)

Foreground process: `Ctrl+C`

Background process:

```bash
pgrep -af "python.*scripts/funda_gateway.py"
pkill -f "python.*scripts/funda_gateway.py"
```

Port troubleshooting only:

```bash
lsof -iTCP:9090 -sTCP:LISTEN -n -P
```
