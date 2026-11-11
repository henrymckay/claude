#!/bin/sh
# Print this plugin's always-on instructions; SessionStart adds stdout to the context.
dir=$(dirname "$0")
cat "$dir/context.md"
case "${CLAUDE_PLUGIN_OPTION_FEEDBACK:-issues}" in
  off) ;;
  file) cat "$dir/feedback-file.md" ;;
  *) cat "$dir/feedback-issues.md" ;;
esac
