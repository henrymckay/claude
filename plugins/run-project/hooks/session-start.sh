#!/bin/sh
# Print this plugin's always-on rules: into a session at SessionStart (plain stdout) and
# into a subagent at SubagentStart (JSON additionalContext, the only form it adds).
# shared.md is identical in every plugin of the marketplace, so it prints once per start of
# a session or subagent: the first of the plugins' hooks to claim that start prints it, and
# the rest print only their own list. A race or a stale marker can repeat the shared rules
# but never drop them: where in doubt, a hook prints.
dir=$(cd "$(dirname "$0")" && pwd -P)
input=$(tr -d '\n')

field() {
  printf '%s' "$input" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p"
}

# Succeeds when this hook should print shared.md.
# A resumed session or subagent still holds the rules from its last start, so the plugin
# that printed them then prints them again, if it is still there: an identical copy, which
# Claude Code does not add twice. Any other start (a startup, a compaction, a new subagent)
# is claimed afresh.
shared_here() {
  session=$(field session_id)
  [ -n "$session" ] || return 0
  base="${TMPDIR:-/tmp}/claude-plugin-rules-$(id -u)"
  mkdir -p "$base" 2>/dev/null
  [ -d "$base" ] && [ -O "$base" ] || return 0
  chmod 700 "$base" 2>/dev/null
  event=$(field hook_event_name)
  how=$(field source)
  id=$(printf '%s' "$session$(field agent_id)" | tr -cd 'A-Za-z0-9._-')
  printer="$base/$id.printer"
  if [ "$event.$how" = SessionStart.resume ] || [ "$event" = SubagentStart ]; then
    last=$(readlink "$printer" 2>/dev/null) && [ -d "$last" ] && { [ "$last" = "$dir" ]; return; }
  fi
  first "$id.$event.$how" || return 1
  rm -f "$printer" && ln -s "$dir" "$printer" 2>/dev/null
  return 0
}

# Succeeds for the first hook of this start to run, and wherever no marker can be kept.
# Each start claims the next generation of its key, a symlink <key>.<n> whose target is the
# time it was made: creating one is atomic, so one hook wins it, and a generation more than
# ten seconds old belongs to an earlier start of the same key, such as an earlier compaction.
first() {
  now=$(date +%s)
  for try in 1 2 3; do
    last=$(ls "$base" | sed -n "s/^$1\.\([0-9][0-9]*\)\$/\1/p" | sort -n | tail -n 1)
    [ -n "$last" ] && fresh "$base/$1.$last" && return 1
    if ln -s "$now" "$base/$1.$((${last:-0} + 1))" 2>/dev/null; then
      find "$base" -type l -mmin +10080 -exec rm -f {} + 2>/dev/null
      return 0
    fi
  done
  return 0
}

# Succeeds when a marker was made within ten seconds of now, either way.
fresh() {
  made=$(readlink "$1" 2>/dev/null) || return 1
  case "$made" in '' | *[!0-9]*) return 1 ;; esac
  age=$((now - made))
  [ "$age" -ge -10 ] && [ "$age" -le 10 ]
}

rules() {
  if shared_here; then
    cat "$dir/shared.md"
    echo
  fi
  cat "$dir/context.md"
  case "${CLAUDE_PLUGIN_OPTION_FEEDBACK:-issues}" in
    off) feedback= ;;
    file) feedback="$dir/feedback-file.md" ;;
    *) feedback="$dir/feedback-issues.md" ;;
  esac
  if [ -n "$feedback" ] && [ -f "$feedback" ]; then
    echo
    cat "$feedback"
  fi
}

case "$(field hook_event_name)" in
  SubagentStart)
    text=$(rules | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' | awk '{ printf "%s%s", (NR > 1 ? "\\n" : ""), $0 }')
    printf '{"hookSpecificOutput":{"hookEventName":"SubagentStart","additionalContext":"%s"}}\n' "$text"
    ;;
  *) rules ;;
esac
