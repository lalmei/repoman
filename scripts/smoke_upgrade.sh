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
# Recreate the old Python template before config.py was retired.
legacy_template="$template/src/repoman/main_template/src/{{python_package_import_name}}/config.py.jinja"
cp "$template/src/repoman/resources/legacy_config.py.jinja" "$legacy_template"
# Model v1 before the retirement migration and the research-pipeline option.
awk '
    /^(_migrations|research_pipeline):/ { omit = 1; next }
    /^[^[:space:]#]/ { omit = 0 }
    /"\/src\/{{ python_package_import_name }}\/config[.]py"/ { next }
    !omit { print }
' "$repo_dir/src/repoman/copier.yml" > "$template/src/repoman/copier.yml"
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
if grep -q '^research_pipeline:' .copier-answers.yml; then
    exit 1
fi
git add .
git -c commit.gpgsign=false commit -qm 'Generated project'
legacy_config=src/upgrade_demo/config.py
test -f "$legacy_config"
git clone -q . "$smoke_dir/pristine"
printf '\n# Project-specific config customization.\n' >> "$legacy_config"
cp "$legacy_config" "$smoke_dir/expected-config.py"
git add "$legacy_config"
git -c commit.gpgsign=false commit -qm 'Customize legacy configuration'
git clone -q . "$smoke_dir/custom-reject"
printf '\nProject-owned instructions.\n' >> AGENTS.md
git add AGENTS.md
git -c commit.gpgsign=false commit -qm 'Customize agent instructions'
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
rm "$legacy_template"
cp "$repo_dir/src/repoman/copier.yml" "$template/src/repoman/copier.yml"
echo 'version two' > "$template/src/repoman/main_template/template-release.txt"
git -C "$template" add .
git -C "$template" -c commit.gpgsign=false commit -qm 'Template version two'
git -C "$template" -c tag.gpgsign=false tag v1.1.0

"$repoman" update . --plan --vcs-ref v1.1.0
test -z "$(git status --porcelain)"
"$repoman" --verbose update . --plan --format json --vcs-ref v1.1.0 > "$smoke_dir/plan.json"
python3 -c 'import json, sys; assert json.load(open(sys.argv[1]))["git_dirty"] is False' "$smoke_dir/plan.json"
touch pending.txt
if "$repoman" update . --plan --format json > "$smoke_dir/plan.json"; then
    exit 1
fi
python3 -c 'import json, sys; assert "dirty_worktree" in json.load(open(sys.argv[1]))["update_readiness"]["blocker_codes"]' "$smoke_dir/plan.json"
rm pending.txt
cp .copier-answers.yml "$smoke_dir/answers.yml"
printf '%s\n' '- invalid answers' > .copier-answers.yml
if "$repoman" inspect --format json > "$smoke_dir/plan.json"; then
    exit 1
fi
python3 -c 'import json, sys; assert "invalid_answers" in json.load(open(sys.argv[1]))["update_readiness"]["blocker_codes"]' "$smoke_dir/plan.json"
mv "$smoke_dir/answers.yml" .copier-answers.yml
"$repoman" update . --vcs-ref v1.1.0 --trust
cmp "$legacy_config" "$smoke_dir/expected-config.py"
"$repoman" update "$smoke_dir/custom-reject" --vcs-ref v1.1.0 --trust --conflict rej
cmp "$smoke_dir/custom-reject/$legacy_config" "$smoke_dir/expected-config.py"
"$repoman" update "$smoke_dir/pristine" --vcs-ref v1.1.0 --trust
test ! -e "$smoke_dir/pristine/$legacy_config"
test -f "$smoke_dir/pristine/src/upgrade_demo/config/main_config.py"
grep -Fx 'research_pipeline: false' .copier-answers.yml
test ! -e research-pipeline-example
test ! -e src/upgrade_demo/cli/commands/run
grep -Fx 'version two' template-release.txt
grep -F 'downstream customization' README.md
grep -Fx 'Project-owned instructions.' AGENTS.md
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
