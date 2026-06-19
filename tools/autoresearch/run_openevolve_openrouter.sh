#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROBLEM_DIR="$ROOT_DIR/tools/autoresearch/openevolve_touchard"
CONFIG="$PROBLEM_DIR/config.openrouter.yaml"
PROFILE="${LATIN_AUTORESEARCH_PROFILE:-smoke}"
METHOD="${LATIN_AUTORESEARCH_METHOD:-touchard}"
ITERATIONS="${LATIN_AUTORESEARCH_ITERATIONS:-5}"
OUTPUT_DIR="${LATIN_AUTORESEARCH_OUTPUT_DIR:-$ROOT_DIR/benchmark_results/autoresearch/openevolve_touchard_smoke}"
ENV_FILE=""
MAX_SECONDS="${LATIN_AUTORESEARCH_MAX_SECONDS:-}"
GRACE_SECONDS="${LATIN_AUTORESEARCH_GRACE_SECONDS:-120}"
CHECKPOINT="${LATIN_AUTORESEARCH_CHECKPOINT:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="${2:?--env-file requires a path}"
      shift 2
      ;;
    --profile)
      PROFILE="${2:?--profile requires a value}"
      shift 2
      ;;
    --method)
      METHOD="${2:?--method requires a value}"
      shift 2
      ;;
    --iterations)
      ITERATIONS="${2:?--iterations requires a value}"
      shift 2
      ;;
    --output)
      OUTPUT_DIR="${2:?--output requires a path}"
      shift 2
      ;;
    --max-seconds)
      MAX_SECONDS="${2:?--max-seconds requires a value}"
      shift 2
      ;;
    --grace-seconds)
      GRACE_SECONDS="${2:?--grace-seconds requires a value}"
      shift 2
      ;;
    --config)
      CONFIG="${2:?--config requires a path}"
      shift 2
      ;;
    --checkpoint)
      CHECKPOINT="${2:?--checkpoint requires a path}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -n "$ENV_FILE" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Env file not found: $ENV_FILE" >&2
    exit 2
  fi
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [[ -z "${OPENROUTER_API_KEY:-}" && -n "${OPENCODE_API_KEY:-}" ]]; then
  export OPENROUTER_API_KEY="$OPENCODE_API_KEY"
fi

if [[ -z "${OPENROUTER_API_KEY:-}" && -n "${OPENAI_API_KEY:-}" ]]; then
  export OPENROUTER_API_KEY="$OPENAI_API_KEY"
fi

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "OPENROUTER_API_KEY is not set. Pass --env-file PATH or export it first." >&2
  exit 2
fi

export LATIN_AUTORESEARCH_PROFILE="$PROFILE"
export LATIN_AUTORESEARCH_METHOD="$METHOD"
export LATIN_AUTORESEARCH_TRACK_MEMORY="${LATIN_AUTORESEARCH_TRACK_MEMORY:-0}"

COMMAND=(
  uvx --from openevolve openevolve-run
  "$PROBLEM_DIR/initial_program.py"
  "$PROBLEM_DIR/evaluator.py"
  --config "$CONFIG"
  --iterations "$ITERATIONS"
  --output "$OUTPUT_DIR"
)

if [[ -n "$CHECKPOINT" ]]; then
  COMMAND+=(--checkpoint "$CHECKPOINT")
fi

if [[ -z "$MAX_SECONDS" ]]; then
  exec "${COMMAND[@]}"
fi

"${COMMAND[@]}" &
CHILD_PID=$!

(
  sleep "$MAX_SECONDS"
  if kill -0 "$CHILD_PID" 2>/dev/null; then
    echo "Time limit reached after ${MAX_SECONDS}s; requesting graceful shutdown..." >&2
    kill -INT "$CHILD_PID" 2>/dev/null || true
    sleep "$GRACE_SECONDS"
    if kill -0 "$CHILD_PID" 2>/dev/null; then
      echo "Grace period expired; terminating run process..." >&2
      kill -TERM "$CHILD_PID" 2>/dev/null || true
    fi
  fi
) &
TIMER_PID=$!

set +e
wait "$CHILD_PID"
STATUS=$?
set -e

kill "$TIMER_PID" 2>/dev/null || true
wait "$TIMER_PID" 2>/dev/null || true
exit "$STATUS"
