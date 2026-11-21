#!/bin/sh
# The PreToolUse guard's entry point. It runs guard.py under the machine's python3, isolated
# from the environment's Python settings. Where no python3 can run, it falls back: with
# nobody present every call is refused, since nothing can check it; with a person present,
# a call whose input names a risky word, after quotes and backslashes are dropped, is asked
# about and the rest go through, so the session stays usable while Python is fixed.
dir=$(cd "$(dirname "$0")" && pwd -P)
input=$(head -c 1048577)
if out=$(printf '%s' "$input" | python3 -I "$dir/guard.py" 2>/dev/null); then
  printf '%s' "$out"
  exit 0
fi
unattended=
if [ "${CLAUDE_GUARD:-}" = deny ] || [ "${CLAUDE_CODE_SESSION_ATTENDED:-}" = 0 ]; then
  unattended=1
fi
case "$input" in *'"permission_mode":"dontAsk"'* | *'"permission_mode":"bypassPermissions"'*) unattended=1 ;; esac
if [ -n "$unattended" ]; then
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Refused by the guard hook (secure-project): python3 could not run, so no call can be checked. Do not retry; report that the guard needs python3."}}'
  exit 0
fi
if [ "${CLAUDE_PLUGIN_OPTION_GUARD:-on}" = off ]; then
  exit 0
fi
plain=$(printf '%s' "$input" | tr -d "\\\\\"'")
if printf '%s' "$plain" | grep -E -i -q 'push|rebase|reset|filter-|update-ref|amend|clean|send-pack|delete|destroy|drop|truncate|purge|trash|[^a-z]rb[^a-z]|rm |printenv|(^|[^a-z_.])env([^a-z_]|$)|secret|token|password|credential|grant[.]json|[.]ssh|id_|[.]pem|[.]key|auth|keyring|security|config|mcp__[a-z0-9_-]*(order|trade|transfer|withdraw|pay|x402|swap|send|reply|forward|share|publish|invite|grant)'; then
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Guard hook (secure-project): python3 could not run, so this call was not checked. Approve only if you meant it."}}'
fi
exit 0
