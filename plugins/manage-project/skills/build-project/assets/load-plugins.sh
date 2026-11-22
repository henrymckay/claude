#!/bin/sh
# SessionStart hook for a Claude Code cloud session: install the plugins from one reviewed commit.
# Copy to .claude/hooks/load-plugins.sh on the project's default branch, register it with
# settings.json beside this file, and fill in the placeholders below.
# It installs nothing unless the marketplace's checkout is exactly the pinned commit and every
# plugin it installs comes from a relative path inside that checkout.
# It prints nothing when every step works. A failed step first undoes what the hook did — the
# plugins it installed, the marketplace it added, the project's settings file as it found it —
# then prints one instruction on standard output and exits 0, since only a SessionStart hook's
# standard output on exit 0 reaches the model; standard error is shown to the user alone.
# It logs nowhere.
[ "${CLAUDE_CODE_REMOTE:-}" = true ] || exit 0

repo='<owner>/<repo>'
sha='<full 40-character commit SHA, reviewed>'
marketplace='<marketplace name>'
plugins='design-project maintain-plugin manage-project run-project structure-app write-code'

settings="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/settings.json"
saved=
added=

undo() {
  for plugin in $plugins; do
    claude plugin uninstall "$plugin@$marketplace" --scope project >/dev/null 2>&1
  done
  claude plugin marketplace remove "$marketplace" >/dev/null 2>&1
  [ -n "$saved" ] && cp "$saved" "$settings"
}

fail() {
  [ -n "$added" ] && undo
  [ -n "$saved" ] && rm -f "$saved"
  echo "Plugins not loaded: $1 Do no work; report this line and stop."
  exit 0
}

case "$sha" in
  *[!0-9a-f]*) fail "the pin is not a full lowercase commit SHA." ;;
esac
[ "${#sha}" -eq 40 ] || fail "the pin is not a full lowercase commit SHA."

if [ -f "$settings" ]; then
  saved=$(mktemp) && cp "$settings" "$saved" || fail "the project's settings could not be saved."
fi

claude plugin marketplace add "$repo#$sha" >/dev/null 2>&1 ||
  fail "adding the marketplace $repo#$sha failed."
added=1

where=$(claude plugin marketplace list --json 2>/dev/null | python3 -c '
import json, sys
found = [m.get("installLocation", "") for m in json.load(sys.stdin) if m.get("name") == sys.argv[1]]
print(found[0] if len(found) == 1 else "")
' "$marketplace") || fail "the marketplace list could not be read."
[ -n "$where" ] && [ -d "$where" ] || fail "the marketplace $marketplace has no checkout."

head=$(git -C "$where" rev-parse HEAD 2>/dev/null) || fail "the checkout's commit could not be read."
[ "$head" = "$sha" ] || fail "the checkout is at $head, not the pinned $sha."

outside=$(python3 -c '
import json, sys
listed = {p.get("name"): p.get("source") for p in json.load(open(sys.argv[1])).get("plugins", [])}
inside = lambda s: isinstance(s, str) and s.startswith("./") and ".." not in s.split("/")
print(" ".join(n for n in sys.argv[2:] if not inside(listed.get(n))))
' "$where/.claude-plugin/marketplace.json" $plugins) || fail "the marketplace's plugin list could not be read."
[ -z "$outside" ] || fail "these plugins are missing or come from outside the pinned commit: $outside."

for plugin in $plugins; do
  claude plugin install "$plugin@$marketplace" --scope project >/dev/null 2>&1 ||
    fail "installing $plugin failed."
done
[ -n "$saved" ] && rm -f "$saved"
exit 0
