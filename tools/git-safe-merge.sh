#!/bin/zsh

set -u

TARGET_BRANCH="${1:-main}"
WORKING_DIR="${2:-}"

if [[ -n "$WORKING_DIR" && -d "$WORKING_DIR" ]]; then
  cd "$WORKING_DIR" || exit 1
else
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  cd "$SCRIPT_DIR" || exit 1
fi

write_abort() {
  local message="$1"
  printf "\n  ABORT: %s\n\n" "$message" >&2
  exit 1
}

write_ok() {
  local message="$1"
  printf "  OK    %s\n" "$message"
}

write_info() {
  local message="$1"
  printf "  INFO  %s\n" "$message"
}

invoke_git() {
  local output
  output="$(git "$@" 2>&1)"
  local status=$?
  printf '%s' "$output"
  return $status
}

separator="  ----------------------------------------"

r="$(invoke_git rev-parse --show-toplevel)"
if [[ $? -ne 0 ]]; then
  write_abort "not inside a git repository"
fi
git_root="$r"

printf "\n  git-safe-merge\n"
printf "%s\n" "$separator"
write_info "repo: $git_root"

r="$(invoke_git status --porcelain)"
if [[ -n "$r" ]]; then
  write_abort "working tree not clean\n\n$r"
fi
write_ok "working tree is clean"

if [[ -f "$git_root/.git/MERGE_HEAD" ]]; then
  write_abort "a merge is currently in progress"
fi

for d in "$git_root/.git/rebase-merge" "$git_root/.git/rebase-apply"; do
  if [[ -e "$d" ]]; then
    write_abort "a rebase is currently in progress"
  fi
done
write_ok "no merge or rebase in progress"

r="$(invoke_git symbolic-ref --short HEAD)"
if [[ $? -ne 0 ]]; then
  write_abort "detached HEAD state -- checkout a branch first"
fi
current_branch="$r"

if [[ "$current_branch" == "$TARGET_BRANCH" ]]; then
  write_abort "current branch is $TARGET_BRANCH -- switch to your working branch first"
fi
write_ok "current branch: $current_branch"

write_info "fetching from origin..."
r="$(invoke_git fetch origin)"
if [[ $? -ne 0 ]]; then
  write_abort "git fetch failed -- check your network connection"
fi

remote_branch="origin/$current_branch"
r="$(invoke_git rev-list --count "$current_branch..$remote_branch")"
if [[ $? -eq 0 && "${r:-0}" -gt 0 ]]; then
  write_abort "$current_branch is $r commit(s) behind $remote_branch -- pull first"
fi
write_ok "$current_branch is up to date with $remote_branch"

remote_target="origin/$TARGET_BRANCH"
r="$(invoke_git rev-parse --verify "$TARGET_BRANCH")"
if [[ $? -ne 0 ]]; then
  write_abort "local branch '$TARGET_BRANCH' does not exist"
fi

r="$(invoke_git rev-list --count "$TARGET_BRANCH..$remote_target")"
if [[ $? -eq 0 && "${r:-0}" -gt 0 ]]; then
  write_abort "local $TARGET_BRANCH is $r commit(s) behind $remote_target -- update $TARGET_BRANCH first"
fi
write_ok "local $TARGET_BRANCH is up to date with $remote_target"

write_info "checking for conflicts..."
r="$(invoke_git merge-tree --write-tree "$TARGET_BRANCH" "$current_branch")"
if [[ $? -ne 0 ]]; then
  conflict_lines="$(printf '%s\n' "$r" | rg '^CONFLICT' || true)"
  file_list=""
  if [[ -n "$conflict_lines" ]]; then
    file_list=$'\n\n  Conflicting files:\n'
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      if [[ "$line" =~ 'CONFLICT'.*:[[:space:]]+(.+)$ ]]; then
        file_list+="    - ${match[1]}\n"
      else
        file_list+="    - $line\n"
      fi
    done <<< "$conflict_lines"
  fi
  write_abort "merge would create conflicts${file_list}"
fi
write_ok "no conflicts detected"

commit_count="$(invoke_git rev-list --count "$TARGET_BRANCH..$current_branch")"
commit_word="commits"
if [[ "${commit_count:-0}" -eq 1 ]]; then
  commit_word="commit"
fi

diff_stat="$(invoke_git diff --stat "$TARGET_BRANCH...$current_branch")"

printf "\n%s\n" "$separator"
printf "  READY TO MERGE\n\n"
printf "  Branch:    %s  ->  %s\n" "$current_branch" "$TARGET_BRANCH"
printf "  Commits:   %s %s\n" "$commit_count" "$commit_word"
printf "  Conflicts: none\n\n"
if [[ -n "$diff_stat" ]]; then
  printf "  Changes:\n"
  while IFS= read -r line; do
    printf "    %s\n" "$line"
  done <<< "$diff_stat"
  printf "\n"
fi

printf "  Merge %s -> %s ? (y/n) " "$current_branch" "$TARGET_BRANCH"
read -r answer
if [[ "$answer" != "y" ]]; then
  printf "\n  Cancelled.\n\n"
  exit 0
fi

printf "\n"
write_info "switching to $TARGET_BRANCH..."
r="$(invoke_git checkout "$TARGET_BRANCH")"
if [[ $? -ne 0 ]]; then
  write_abort "failed to checkout $TARGET_BRANCH"
fi

write_info "merging $current_branch..."
r="$(invoke_git merge "$current_branch")"
if [[ $? -ne 0 ]]; then
  printf "  %s\n" "$r" >&2
  git checkout "$current_branch" >/dev/null 2>&1 || true
  write_abort "merge failed -- switched back to $current_branch"
fi

write_info "pushing to origin/$TARGET_BRANCH..."
r="$(invoke_git push origin "$TARGET_BRANCH")"
if [[ $? -ne 0 ]]; then
  printf "  %s\n" "$r" >&2
  write_abort "push failed -- you are now on $TARGET_BRANCH with the merge applied locally"
fi

write_info "switching back to $current_branch..."
git checkout "$current_branch" >/dev/null 2>&1 || true

printf "\n%s\n" "$separator"
printf "  DONE\n"
printf "  %s merged into %s and pushed to origin\n\n" "$current_branch" "$TARGET_BRANCH"
