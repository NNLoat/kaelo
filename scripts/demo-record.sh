#!/usr/bin/env bash
# Record the Cassette: run every query in demo/queries.txt live, then every
# generation in demo/generations.txt, and print the results for review.
# Needs network + AWS credentials (.env). Does NOT commit anything; review the
# output, then `git add demo/fixtures`.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/demo-env.sh
demo_up record

work=$(mktemp -d)
jar="$work/jar"
trap 'rm -rf "$work"' EXIT
JSON='Content-Type: application/json'
curl -fsS -c "$jar" -o /dev/null -X POST "$API/api/auth/login" -H "$JSON" \
  -d "{\"username\":\"$DEMO_USER\",\"password\":\"$DEMO_PASSWORD\"}"

failed=0
fail() { echo "FAILED: $*" >&2; failed=1; }
blank_or_comment() { [[ -z "${1//[[:space:]]/}" || "$1" == \#* ]]; }
trim() { local v="$1"; v="${v#"${v%%[![:space:]]*}"}"; echo "${v%"${v##*[![:space:]]}"}"; }

# --- searches (inline live scoring is slow: 15 minutes per query) ---------------
n=0
while IFS= read -r query || [ -n "$query" ]; do
  blank_or_comment "$query" && continue
  n=$((n + 1))
  echo; echo "== $query"
  body=$(python3 -c 'import json,sys; print(json.dumps({"query": sys.argv[1]}))' "$query")
  out="$work/q$n.json"
  code=$(curl -sS -m 900 -b "$jar" -o "$out" -w '%{http_code}' -X POST "$API/api/papers/search" \
    -H "$JSON" -d "$body") || code=000
  if [ "$code" != 200 ]; then fail "search HTTP $code"; cat "$out" >&2; continue; fi
  printf '%s' "$query" > "$work/q$n.query"
  python3 - "$out" <<'PY' || failed=1
import json, sys
papers = json.load(open(sys.argv[1]))["papers"]
if not papers:
    print("FAILED: empty result", file=sys.stderr); sys.exit(1)
for i, p in enumerate(papers, 1):
    v = p["final"]["value"]
    print(f"{i:>2}. {p['title'][:90]:<90}  {'-' if v is None else f'{v:.3f}'}")
PY
done < demo/queries.txt

# --- generation jobs: start one, wait for it to finish ----------------------------
run_job() {  # run_job <paper_ref> <case>
  local ref="$1" gcase="$2" job id state i
  job=$(curl -fsS -b "$jar" -X POST "$API/api/codegen/jobs" -H "$JSON" \
    -d "{\"paper_ref\":\"$ref\",\"case\":\"$gcase\"}") || { fail "could not start $gcase for $ref"; return; }
  id=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<<"$job")
  for i in $(seq 1 200); do  # up to ~10 minutes
    job=$(curl -fsS -b "$jar" "$API/api/codegen/jobs/$id")
    state=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["state"])' <<<"$job")
    case "$state" in
      succeeded) echo "   $gcase $ref: succeeded"; return ;;
      failed | refused | cancelled) fail "$gcase $ref: $state: $job"; return ;;
    esac
    sleep 3
  done
  fail "$gcase $ref: still $state after 10 minutes"
}

# Pick the paper whose title contains $2 (case-insensitive) from query $1's results.
paper_id() {  # paper_id <query> <title fragment>
  local f
  for f in "$work"/q*.query; do
    [ "$(cat "$f")" = "$1" ] || continue
    python3 - "${f%.query}.json" "$2" <<'PY'
import json, sys
hits = [p for p in json.load(open(sys.argv[1]))["papers"] if sys.argv[2].lower() in p["title"].lower()]
if len(hits) != 1:
    sys.exit(f"{len(hits)} papers match {sys.argv[2]!r}, need exactly 1")
print(hits[0]["id"])
PY
    return
  done
  echo "query not found in demo/queries.txt: $1" >&2; return 1
}

echo; echo "== generations"
while IFS= read -r line || [ -n "$line" ]; do
  blank_or_comment "$line" && continue
  IFS='|' read -r kind a b c <<<"$line"
  kind=$(trim "$kind"); a=$(trim "$a"); b=$(trim "$b"); c=$(trim "${c:-}")
  case "$kind" in
    reader)  # reader | <query> | <case> | <title fragment>
      id=$(paper_id "$a" "$c") || { fail "reader line '$line'"; continue; }
      run_job "$id" "$b" ;;
    writer)  # writer | <paper ref> | <manuscript PDF>   (always a review)
      [ -f "$b" ] || { fail "no such file: $b"; continue; }
      claim=$(curl -fsS -b "$jar" -X POST "$API/api/writer/claims" -H "$JSON" \
        -d "{\"paper_ref\":\"$a\"}") || { fail "claim $a"; continue; }
      cid=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<<"$claim")
      curl -fsS -b "$jar" -o /dev/null -F "file=@$b;type=application/pdf" \
        "$API/api/writer/claims/$cid/manuscript" || { fail "manuscript upload $b"; continue; }
      run_job "$a" review ;;
    *) fail "unknown line kind '$kind'" ;;
  esac
done < demo/generations.txt

# The container writes the Cassette as root; hand it to the invoking user.
docker compose exec -T backend chown "$(id -u):$(id -g)" /demo/fixtures/cassette.json || true

[ "$failed" = 0 ] || { echo "one or more steps failed; Cassette is incomplete" >&2; exit 1; }
echo
echo "Recorded. Review the order above, then: git add demo/fixtures/cassette.json"
