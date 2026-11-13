#!/usr/bin/env bash
set -euo pipefail

repoman="$1"
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
smoke_dir="$(mktemp -d)"
trap 'rm -rf "$smoke_dir"' EXIT
export GIT_AUTHOR_NAME="Repoman smoke test"
export GIT_AUTHOR_EMAIL="repoman@example.invalid"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

template="$smoke_dir/template"
mkdir -p "$template/src"
cp "$repo_dir/copier.yml" "$template/"
cp -R "$repo_dir/src/repoman" "$template/src/"
cp "$repo_dir/.gitignore" "$template/"
git -C "$template" init -q
echo 'version one' > "$template/src/repoman/main_template/template-release.txt"
git -C "$template" add .
git -C "$template" -c commit.gpgsign=false commit -qm 'Template version one'
git -C "$template" -c tag.gpgsign=false tag v1.0.0

cd "$smoke_dir"
"$repoman" create -pn upgrade-demo --preset cli --template "$template" --vcs-ref v1.0.0 --trust
cd upgrade-demo
"$repoman" generator add sample --trust
command_file=src/upgrade_demo/cli/commands/sample/__init__.py
extension_answers=.repoman/extensions/command/sample.answers.yml
grep -Fx '_commit: v1.0.0' "$extension_answers"
git add .
git -c commit.gpgsign=false commit -qm 'Generated project'
printf '\ndownstream customization\n' >> README.md
git add README.md
git -c commit.gpgsign=false commit -qm 'Customize generated README'

command_templates=("$template"/src/repoman/extentions/command_template/*/src/*/cli/commands/*/__init__.py.jinja)
command_template="${command_templates[0]}"
{
    echo '# Extension template version two'
    cat "$command_template"
} > "$smoke_dir/command-v2"
mv "$smoke_dir/command-v2" "$command_template"
printf '\n# Downstream command customization\n' >> "$command_file"
git add "$command_file"
git -c commit.gpgsign=false commit -qm 'Customize generated command'
echo 'version two' > "$template/src/repoman/main_template/template-release.txt"
git -C "$template" add .
git -C "$template" -c commit.gpgsign=false commit -qm 'Template version two'
git -C "$template" -c tag.gpgsign=false tag v1.1.0

"$repoman" update . --plan --vcs-ref v1.1.0
test -z "$(git status --porcelain)"
"$repoman" update . --vcs-ref v1.1.0 --trust
grep -Fx 'version two' template-release.txt
grep -F 'downstream customization' README.md
grep -Fx '_commit: v1.1.0' .copier-answers.yml
git add .
git -c commit.gpgsign=false commit -qm 'Review and accept template upgrade'

"$repoman" extensions sync --vcs-ref v1.1.0 --trust .
grep -F 'Extension template version two' "$command_file"
grep -F 'Downstream command customization' "$command_file"
grep -Fx '_commit: v1.1.0' "$extension_answers"
git add .
git -c commit.gpgsign=false commit -qm 'Review and accept command upgrade'
"$repoman" extensions sync --vcs-ref v1.1.0 --trust .
test -z "$(git status --porcelain)"

"$repoman" update . --vcs-ref v1.1.0 --trust
test -z "$(git status --porcelain)"
