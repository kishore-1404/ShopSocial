#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE="docker compose"
PROJECT_NAME="shopsocial"
SMOKE_USER="smoke_$(date +%s)"
SMOKE_PASSWORD="SmokePass123!"
SMOKE_EMAIL="${SMOKE_USER}@example.com"
KEEP_UP="${SMOKE_KEEP_UP:-0}"

for cmd in docker curl python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd"
    exit 1
  fi
done

cleanup() {
  if [ "$KEEP_UP" != "1" ]; then
    $COMPOSE down --remove-orphans >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

dump_diagnostics() {
  echo "[smoke] ---- compose status ----"
  $COMPOSE ps || true
  echo "[smoke] ---- recent service logs ----"
  $COMPOSE logs --no-color --tail=120 user product order chat order_worker db redis || true
}

choose_service_jwt() {
  local current="${SERVICE_JWT_SECRET:-}"
  if [ "${#current}" -ge 32 ]; then
    printf '%s' "$current"
    return
  fi
  python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
}

export SERVICE_JWT_SECRET="$(choose_service_jwt)"

echo "[smoke] Starting compose services"
$COMPOSE up -d --build db redis user product order chat order_worker

wait_http_any() {
  local url="$1"
  local attempts="${2:-60}"
  local sleep_seconds="${3:-2}"
  local label="${4:-$url}"
  local i
  for i in $(seq 1 "$attempts"); do
    code="$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)"
    if [ "$code" != "000" ]; then
      echo "[smoke] ${label} reachable (HTTP ${code})"
      return 0
    fi
    echo "[smoke] waiting for ${label} (${i}/${attempts})"
    sleep "$sleep_seconds"
  done
  echo "[smoke] timed out waiting for ${label}: ${url}"
  dump_diagnostics
  return 1
}

echo "[smoke] Waiting for HTTP services"
wait_http_any "http://localhost:8000/api/accounts/register/" 90 2 "user service"
wait_http_any "http://localhost:5000/healthz" 90 2 "product service"
wait_http_any "http://localhost:7000/" 90 2 "order service"

echo "[smoke] Registering smoke user"
register_payload="$(python3 - <<PY
import json
print(json.dumps({
  "username": "$SMOKE_USER",
  "email": "$SMOKE_EMAIL",
  "password": "$SMOKE_PASSWORD"
}))
PY
)"

register_status="$(curl -s -o /tmp/smoke_register.json -w "%{http_code}" \
  -X POST "http://localhost:8000/api/accounts/register/" \
  -H "Content-Type: application/json" \
  -d "$register_payload")"

if [ "$register_status" != "201" ]; then
  echo "Register failed with HTTP $register_status"
  cat /tmp/smoke_register.json
  exit 1
fi

echo "[smoke] Obtaining user access token"
auth_payload="$(python3 - <<PY
import json
print(json.dumps({
  "username": "$SMOKE_USER",
  "password": "$SMOKE_PASSWORD"
}))
PY
)"

auth_status="$(curl -s -o /tmp/smoke_auth.json -w "%{http_code}" \
  -X POST "http://localhost:8000/api/auth/" \
  -H "Content-Type: application/json" \
  -d "$auth_payload")"

if [ "$auth_status" != "200" ]; then
  echo "Auth failed with HTTP $auth_status"
  cat /tmp/smoke_auth.json
  exit 1
fi

USER_JWT="$(python3 - <<'PY'
import json
with open('/tmp/smoke_auth.json', 'r', encoding='utf-8') as f:
    print(json.load(f)['access'])
PY
)"

echo "[smoke] Verifying protected user endpoint"
user_profile_status="$(curl -s -o /tmp/smoke_profile.json -w "%{http_code}" \
  "http://localhost:8000/api/accounts/profile/" \
  -H "Authorization: Bearer ${USER_JWT}")"
if [ "$user_profile_status" != "200" ]; then
  echo "User profile check failed with HTTP $user_profile_status"
  cat /tmp/smoke_profile.json
  exit 1
fi

echo "[smoke] Creating service JWT inside order container"
SERVICE_JWT="$($COMPOSE exec -T order python - <<'PY'
import os
import time
import jwt
secret = os.environ['SERVICE_JWT_SECRET']
token = jwt.encode({"sub": "compose-smoke", "iat": int(time.time())}, secret, algorithm="HS256")
print(token)
PY
)"

echo "[smoke] Verifying protected product GraphQL endpoint"
product_status="$(curl -s -o /tmp/smoke_product.json -w "%{http_code}" \
  -X POST "http://localhost:5000/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SERVICE_JWT}" \
  -d '{"query":"{ hello }"}')"
if [ "$product_status" != "200" ]; then
  echo "Product GraphQL check failed with HTTP $product_status"
  cat /tmp/smoke_product.json
  exit 1
fi
python3 - <<'PY'
import json
with open('/tmp/smoke_product.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)
if payload.get('data', {}).get('hello') != 'Hello, ShopSocial!':
    raise SystemExit('Unexpected GraphQL response payload')
PY

echo "[smoke] Verifying protected order API endpoint"
order_status="$(curl -s -o /tmp/smoke_order_create.json -w "%{http_code}" \
  -X POST "http://localhost:7000/orders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SERVICE_JWT}" \
  -d '{"user_id":1,"product_ids":[101,102],"total":49.99}')"
if [ "$order_status" != "201" ]; then
  echo "Order create check failed with HTTP $order_status"
  cat /tmp/smoke_order_create.json
  exit 1
fi

ORDER_ID="$(python3 - <<'PY'
import json
with open('/tmp/smoke_order_create.json', 'r', encoding='utf-8') as f:
    print(json.load(f)['order']['id'])
PY
)"

order_get_status="$(curl -s -o /tmp/smoke_order_get.json -w "%{http_code}" \
  "http://localhost:7000/orders/${ORDER_ID}" \
  -H "Authorization: Bearer ${SERVICE_JWT}")"
if [ "$order_get_status" != "200" ]; then
  echo "Order get check failed with HTTP $order_get_status"
  cat /tmp/smoke_order_get.json
  exit 1
fi

echo "[smoke] Verifying chat connect and join flow"
$COMPOSE exec -T -e SMOKE_JWT="$SERVICE_JWT" chat python - <<'PY'
import asyncio
import json
import os
import websockets

async def main() -> None:
    token = os.environ["SMOKE_JWT"]
    async with websockets.connect(
        "ws://127.0.0.1:9000",
      additional_headers={"Authorization": f"Bearer {token}"},
    ) as ws:
        await ws.send(json.dumps({"action": "join", "product_id": 123}))
        response = json.loads(await ws.recv())
        info = response.get("info", "")
        if "Joined room 123" not in info:
            raise RuntimeError(f"Unexpected join response: {response}")

asyncio.run(main())
PY

echo "[smoke] Compose integration smoke checks passed"
if [ "$KEEP_UP" = "1" ]; then
  echo "[smoke] Services kept running because SMOKE_KEEP_UP=1"
fi
