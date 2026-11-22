#!/bin/sh
# SessionStart hook for a Claude Code cloud session: install the plugins from one reviewed commit.
# Copy to .claude/hooks/load-plugins.sh on the project's default branch, register it with
# settings.json beside this file, and fill in the placeholders below.
# It prints nothing when every step works, since a SessionStart hook's output reaches the
# session; a failed step prints one line, so the session can report it. It logs nowhere.
[ "${CLAUDE_CODE_REMOTE:-}" = true ] || exit 0

source='<owner>/<repo>#<full 40-character commit SHA, reviewed>'
marketplace='<marketplace name>'
plugins='design-project maintain-plugin manage-project run-project structure-app write-code'

if ! claude plugin marketplace add "$source" >/dev/null 2>&1; then
  echo "Plugins not loaded: adding the marketplace $source failed."
  exit 0
fi
for plugin in $plugins; do
  claude plugin install "$plugin@$marketplace" --scope project >/dev/null 2>&1 ||
    echo "Plugin $plugin not loaded: its install failed."
done
exit 0
