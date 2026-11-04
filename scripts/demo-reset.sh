#!/usr/bin/env bash
# Reset the app to the known demo state: empty DB, DEMO_MODE=replay, demo account.
# Needs no network or AWS credentials once the Cassette is committed.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/demo-env.sh
demo_up replay
