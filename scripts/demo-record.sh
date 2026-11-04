#!/usr/bin/env bash
# Record the Cassette: run every query in demo/queries.txt live and print the
# ordered results for review. Needs network + AWS credentials (.env).
# Does NOT commit anything; review the output, then `git add demo/fixtures`.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/demo-env.sh
demo_up record

jar=$(mktemp)
trap 'rm -f "$jar"' EXIT
curl -fsS -c "$jar" -o /dev/null -X POST "$API/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$DEMO_USER\",\"password\":\"$DEMO_PASSWORD\"}"

failed=0
while IFS= read -r query || [ -n "$query" ]; do
  [[ -z "${query//[[:space:]]/}" || "$query" == \#* ]] && continue
  echo
  echo "== $query"
  body=$(python3 -c 'import json,sys; print(json.dumps({"query": sys.argv[1]}))' "$query")
  out=$(mktemp)
  # Inline live scoring is slow: allow 15 minutes per query.
  code=$(curl -sS -m 900 -b "$jar" -o "$out" -w '%{http_code}' -X POST "$API/api/papers/search" \
    -H 'Content-Type: application/json' -d "$body") || code=000
  if [ "$code" != 200 ]; then
    echo "FAILED: HTTP $code" >&2; cat "$out" >&2; rm -f "$out"; failed=1; continue
  fi
  python3 - "$out" <<'PY' || failed=1
import json, sys
papers = json.load(open(sys.argv[1]))["papers"]
if not papers:
    print("FAILED: empty result", file=sys.stderr); sys.exit(1)
for i, p in enumerate(papers, 1):
    v = p["final"]["value"]
    print(f"{i:>2}. {p['title'][:90]:<90}  {'-' if v is None else f'{v:.3f}'}")
PY
  rm -f "$out"
done < demo/queries.txt

# The container writes the Cassette as root; hand it to the invoking user.
docker compose exec -T backend chown "$(id -u):$(id -g)" /demo/fixtures/cassette.json || true

[ "$failed" = 0 ] || { echo "one or more queries failed; Cassette is incomplete" >&2; exit 1; }
echo
echo "Recorded. Review the order above, then: git add demo/fixtures/cassette.json"
