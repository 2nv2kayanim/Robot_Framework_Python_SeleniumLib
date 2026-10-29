#!/usr/bin/env bash
set -euo pipefail

result="NOT STARTED"
build_url="Unavailable"

write_summary() {
  {
    printf '### Jenkins test run\n\n'
    printf -- '- Build URL: %s\n' "$build_url"
    printf -- '- Result: %s\n' "$result"
  } >> "$GITHUB_STEP_SUMMARY"
  {
    printf 'build_url=%s\n' "$build_url"
    printf 'result=%s\n' "$result"
  } >> "$GITHUB_OUTPUT"
}

on_exit() {
  exit_code=$?
  if [[ -n "${headers:-}" ]]; then
    rm -f "$headers"
  fi
  if [[ $exit_code -ne 0 ]]; then
    case "$result" in
      "ABORTED in queue"|"TIMED OUT waiting in queue"|"TIMED OUT while build was running")
        ;;
      "FAILURE"|"ABORTED"|"UNSTABLE")
        ;;
      *)
        result="FAILED (exit ${exit_code})"
        ;;
    esac
  fi
  write_summary
}
trap on_exit EXIT

: "${JENKINS_URL:?Set the JENKINS_URL repository variable.}"
: "${JENKINS_JOB_NAME:?Set the JENKINS_JOB_NAME repository variable.}"
: "${JENKINS_USER:?Set the JENKINS_USER repository secret.}"
: "${JENKINS_API_TOKEN:?Set the JENKINS_API_TOKEN repository secret.}"
: "${REPO_URL:?The repository URL was not provided.}"
: "${GIT_REF:?The triggering Git ref was not provided.}"
: "${GIT_SHA:?The triggering commit SHA was not provided.}"

if [[ "$JENKINS_URL" != https://* ]]; then
  printf 'JENKINS_URL must use HTTPS to protect API credentials.\n' >&2
  exit 1
fi

job_path=$(jq -rn --arg job "$JENKINS_JOB_NAME" '$job | split("/") | map(@uri) | join("/job/")')
endpoint="${JENKINS_URL%/}/job/${job_path}/buildWithParameters"
headers=$(mktemp)

http_status=$(curl --silent --show-error --user "$JENKINS_USER:$JENKINS_API_TOKEN" \
  --request POST \
  --data-urlencode "REPO_URL=$REPO_URL" \
  --data-urlencode "GIT_REF=$GIT_REF" \
  --data-urlencode "GIT_SHA=$GIT_SHA" \
  --dump-header "$headers" \
  --output /dev/null \
  --write-out '%{http_code}' \
  "$endpoint")
if [[ "$http_status" != "201" && "$http_status" != "302" ]]; then
  printf 'Jenkins returned HTTP %s when queueing the build.\n' "$http_status" >&2
  exit 1
fi

queue_location=$(awk 'tolower($1) == "location:" {gsub("\r", ""); print $2; exit}' "$headers")
if [[ -z "$queue_location" ]]; then
  printf 'Jenkins did not return a queue Location header.\n' >&2
  exit 1
fi
if [[ "$queue_location" != https://* ]]; then
  if [[ "$queue_location" == http://* ]]; then
    printf 'Jenkins returned an insecure HTTP queue Location.\n' >&2
    exit 1
  fi
  queue_location="${JENKINS_URL%/}/${queue_location#/}"
fi

queue_deadline=$((SECONDS + 900))
queue_payload=""
while (( SECONDS < queue_deadline )); do
  queue_payload=$(curl --silent --show-error --fail \
    --user "$JENKINS_USER:$JENKINS_API_TOKEN" \
    "${queue_location%/}/api/json") || {
      printf 'Unable to read the Jenkins queue item.\n' >&2
      exit 1
    }
  if [[ $(jq -r '.cancelled // false' <<< "$queue_payload") == "true" ]]; then
    result="ABORTED in queue"
    printf 'The Jenkins queue item was cancelled.\n' >&2
    exit 1
  fi
  build_url=$(jq -r '.executable.url // empty' <<< "$queue_payload")
  if [[ -n "$build_url" ]]; then
    break
  fi
  sleep 5
done
if [[ -z "$build_url" || "$build_url" == "Unavailable" ]]; then
  result="TIMED OUT waiting in queue"
  printf 'Jenkins did not assign a build within 15 minutes.\n' >&2
  exit 1
fi

build_deadline=$((SECONDS + 5400))
while (( SECONDS < build_deadline )); do
  build_payload=$(curl --silent --show-error --fail \
    --user "$JENKINS_USER:$JENKINS_API_TOKEN" \
    "${build_url%/}/api/json") || {
      printf 'Unable to read the Jenkins build status.\n' >&2
      exit 1
    }
  result=$(jq -r '.result // "RUNNING"' <<< "$build_payload")
  if [[ "$result" != "RUNNING" ]]; then
    break
  fi
  sleep 10
done

if [[ "$result" == "RUNNING" ]]; then
  result="TIMED OUT while build was running"
  printf 'Jenkins build exceeded the 90-minute monitoring limit.\n' >&2
  exit 1
fi
if [[ "$result" != "SUCCESS" ]]; then
  printf 'Jenkins build completed with result %s.\n' "$result" >&2
  exit 1
fi
