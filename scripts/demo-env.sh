#!/usr/bin/env bash
# Sourced by demo-reset.sh and demo-record.sh so record and replay always agree.
# Shell env overrides .env for compose interpolation, so .env is never edited.
# (spec demo-mode, R7)

export QUERY_EXPANSION_ENABLED=false   # no LLM query rewrite
export CODEGEN_MOCK=false              # real code generation/review, answered from the Cassette

# Fixed, non-secret, local-only demo account (username 3-32, password 8-128 chars).
DEMO_USER="demo"
DEMO_PASSWORD="demo-password"
API="http://localhost:${BACKEND_PORT:-8000}"

wait_healthy() {  # poll GET /health, at most 120 s
  local i
  for i in $(seq 1 60); do
    curl -fsS "$API/health" >/dev/null 2>&1 && return 0
    sleep 2
  done
  echo "backend did not become healthy within 120 s" >&2
  return 1
}

# demo_up <record|replay>: wipe the stack (incl. the DB volume), start it in the
# given mode, wait for health, and make sure the demo account exists.
demo_up() {
  export DEMO_MODE="$1"
  docker compose down -v
  docker compose up -d --build
  wait_healthy
  local code
  code=$(curl -sS -o /dev/null -w '%{http_code}' -X POST "$API/api/auth/register" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"$DEMO_USER\",\"password\":\"$DEMO_PASSWORD\"}")
  case "$code" in 201 | 409) ;; *) echo "register failed: HTTP $code" >&2; return 1 ;; esac
  echo "demo ready: DEMO_MODE=$DEMO_MODE, user=$DEMO_USER"
}
