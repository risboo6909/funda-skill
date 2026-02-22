---
name: funda
description: Access Funda listings via a local HTTP gateway built on pyfunda
compatibility: Python3, access to internet
---

# SKILL: Funda Gateway (pyfunda-based HTTP Service)

## Overview

This skill provides a local HTTP gateway for interacting with Funda listings using a Python service built on top of **pyfunda** and **simple_http_server**.

The service exposes REST endpoints to:
- Fetch a single listing by public ID
- Fetch price history for a listing
- Search listings using common Funda filters

The skill is intended for **local or trusted environments only**.

---

## Reference

- Funda client implementation and parameters are based on:
  https://github.com/0xMH/pyfunda

---

## Preconditions

The agent must ensure:

1. Python **3.10+**
2. Required dependencies installed:
   - `simple_http_server`
   - `pyfunda` (or compatible local `funda` module)
4. Network access to Funda endpoints

If dependencies are missing, the agent must install them before proceeding.

---

## Launch Instructions

Start the server using:

```bash
python gateway.py --port 9090 --timeout 10
```

### Arguments

| Argument | Type | Default | Description |
|--------|------|---------|-------------|
| `--port` | int | 9090 | TCP port to bind the HTTP server |
| `--timeout` | int | 10 | Timeout (seconds) for upstream Funda API calls |

### Expected Behavior
- Process runs in foreground
- Server listens on the specified port
- No output implies successful startup

If the port is already in use, the agent must retry with another port.

---

## Health Check

There is no explicit `/health` endpoint.

To validate server availability, the agent must call:

```bash
GET /search_listings
```

Expected result:
- HTTP 200
- Valid JSON object (can be empty)

---

## API Endpoints

### 1. Get Listing

**Endpoint**
```
GET /get_listing/{public_id}
```

**Description**
Returns full listing details for a given Funda public ID.

**Example**
```bash
curl http://localhost:9090/get_listing/43242669
```

**Response**
- JSON object returned by `listing.to_dict()`

---

### 2. Get Price History

**Endpoint**
```
GET /get_price_history/{public_id}
```

**Description**
Returns historical price changes for a listing.

---

### 3. Search Listings

**Endpoint**
```
GET or POST /search_listings
```

---

## Supported Search Parameters

See pyfunda reference for exact semantics.

---

## Security Notes

- No authentication
- No rate limiting
- Must NOT be exposed publicly

---

## Skill Classification

- Type: Local HTTP Tool
- State: Stateless
