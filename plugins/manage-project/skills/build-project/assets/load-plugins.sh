#!/bin/sh
# SessionStart hook for a Claude Code cloud session: install the plugins from one reviewed commit.
# Copy to .claude/hooks/load-plugins.sh on the project's default branch, register it with
# settings.json beside this file, and fill in the placeholders below.
# It installs nothing unless the marketplace's checkout is exactly the pinned commit.
# It prints nothing when every step works, since a SessionStart hook's output reaches the
# session; a failed step prints one line to standard error and exits 1. It logs nowhere.
[ "${CLAUDE_CODE_REMOTE:-}" = true ] || exit 0

repo='<owner>/<repo>'
sha='<full 40-character commit SHA, reviewed>'
marketplace='<marketplace name>'
plugins='design-project maintain-plugin manage-project run-project structure-app write-code'

fail() {
  echo "Plugins not loaded: $1" >&2
  exit 1
}

case "$sha" in
  *[!0-9a-f]*) fail "the pin is not a full lowercase commit SHA." ;;
esac
[ "${#sha}" -eq 40 ] || fail "the pin is not a full lowercase commit SHA."

claude plugin marketplace add "$repo#$sha" >/dev/null 2>&1 ||
  fail "adding the marketplace $repo#$sha failed."

where=$(claude plugin marketplace list --json 2>/dev/null | python3 -c '
import json, sys
found = [m.get("installLocation", "") for m in json.load(sys.stdin) if m.get("name") == sys.argv[1]]
print(found[0] if len(found) == 1 else "")
' "$marketplace") || fail "the marketplace list could not be read."
[ -n "$where" ] && [ -d "$where" ] || fail "the marketplace $marketplace has no checkout."

head=$(git -C "$where" rev-parse HEAD 2>/dev/null) || fail "the checkout's commit could not be read."
[ "$head" = "$sha" ] || fail "the checkout is at $head, not the pinned $sha."

for plugin in $plugins; do
  claude plugin install "$plugin@$marketplace" --scope project >/dev/null 2>&1 ||
    fail "installing $plugin failed."
done
exit 0
