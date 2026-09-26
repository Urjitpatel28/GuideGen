#!/usr/bin/env sh
# Creates the skill discovery symlinks (.claude/.agents/.opencode -> skills/guidegen).
set -e
cd "$(dirname "$0")/.."
for dir in .claude/skills .agents/skills .opencode/skills; do
  mkdir -p "$dir"
  [ -e "$dir/guidegen" ] || ln -s ../../skills/guidegen "$dir/guidegen"
  echo "linked $dir/guidegen"
done
