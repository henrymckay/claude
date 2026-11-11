#!/bin/sh
# Print this plugin's always-on instructions; SessionStart adds stdout to the context.
dir=$(dirname "$0")
cat "$dir/context.md"
