#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
smoke_dir="$(mktemp -d)"
trap 'rm -rf "$smoke_dir"' EXIT
export GIT_AUTHOR_NAME="Repoman smoke test"
export GIT_AUTHOR_EMAIL="repoman@example.invalid"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

commit_all() {
    git add -A
    git -c commit.gpgsign=false commit -qm "$1"
}

# Package the same tagged template tree that the installed wheel will record.
mkdir "$smoke_dir/template"
cd "$smoke_dir/template"
cp "$repo_dir"/{copier.yml,pyproject.toml,README.md,LICENSE,.gitignore} .
mkdir src
cp -R "$repo_dir/src/repoman" src/
git init -q
commit_all "Template version one"
git -c tag.gpgsign=false tag v1.0.0
git rev-parse HEAD > src/repoman/resources/template_revision.txt
uv build --wheel --out-dir "$smoke_dir/dist"
rm src/repoman/resources/template_revision.txt
uv venv --python 3.12 "$smoke_dir/venv"
uv pip install --python "$smoke_dir/venv/bin/python" "$smoke_dir"/dist/*.whl
repoman="$smoke_dir/venv/bin/repoman"

layout=src/layouts/Site.astro
python3 - "$layout" <<'PY'
from pathlib import Path
import sys

root = Path("src/repoman/astro_template/template")
layout = root / sys.argv[1]
layout.write_text(layout.read_text().replace('<nav class="site-nav">', '<nav class="site-nav" aria-label="Site">'))
# Change both existing protected files upstream to exercise the preservation rule.
profile = root / "src/content/profile.json.jinja"
profile.write_text(profile.read_text().replace("Write a short introduction here.", "Introduce yourself here."))
css = root / "src/styles/custom.css"
css.write_text(css.read_text().replace("Put your", "Add your"))
PY
commit_all "Template version two"
git -c tag.gpgsign=false tag v1.1.0
git clone --quiet --bare --no-local . "$smoke_dir/template.git"
v1="$(git rev-parse v1.0.0)"
cd "$smoke_dir"
rm -rf template
# Mirror the release URL locally so the test needs no published tags.
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="url.file://$smoke_dir/template.git.insteadOf"
export GIT_CONFIG_VALUE_0="https://github.com/lalmei/repoman.git"

"$repoman" --dry-run create astro preview
test ! -e preview
"$repoman" create astro personal-site
cd personal-site
grep -Fx "_commit: $v1" .copier-answers.yml
grep -Fx "_src_path: $GIT_CONFIG_VALUE_0" .copier-answers.yml
grep -Fx 'repoman_astro: true' .copier-answers.yml
git init -q
commit_all "Generated site"
cp -R . "$smoke_dir/overlap"

profile=src/content/profile.json
project=src/content/projects/observatory.md
image=public/images/observatory.svg
css=src/styles/custom.css
cat > "$profile" <<'JSON'
{
  "name": "Casey Taylor",
  "bio": "I build tools for small observatories.",
  "links": [{ "label": "Contact", "url": "https://example.org/contact" }]
}
JSON
cat > "$project" <<'MARKDOWN'
---
title: Observatory log
url: https://example.org/log
---

A log for nights at the telescope.

![Observatory](/images/observatory.svg)
MARKDOWN
cat > "$image" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"/></svg>
SVG
printf 'h1 { letter-spacing: 0.03em; }\n' >> "$css"
rm src/content/projects/example.md
python3 - "$layout" <<'PY'
from pathlib import Path
import sys

layout = Path(sys.argv[1])
layout.write_text(layout.read_text().replace("<main>", '<main class="local-layout">'))
PY
commit_all "Customize personal site"

"$repoman" update . --plan --format json --vcs-ref v1.1.0 > "$smoke_dir/plan.json"
grep -F "$GIT_CONFIG_VALUE_0" "$smoke_dir/plan.json"
grep -F 'v1.1.0' "$smoke_dir/plan.json"
test -z "$(git status --porcelain)"
"$repoman" update . --vcs-ref v1.1.0
git diff --exit-code HEAD -- "$profile" "$project" "$image" "$css"
test ! -e src/content/projects/example.md
grep -F 'aria-label="Site"' "$layout"
grep -F 'class="local-layout"' "$layout"
grep -Fx '_commit: v1.1.0' .copier-answers.yml
grep -Fx 'repoman_astro: true' .copier-answers.yml
npm ci
npm run check
npm run build
grep -qF 'I build tools for small observatories.' dist/index.html
grep -qF 'https://example.org/log' dist/index.html
grep -qF 'aria-label="Site"' dist/index.html
cmp "$image" "dist/images/observatory.svg"
commit_all "Accept template update"
"$repoman" update . --vcs-ref v1.1.0
test -z "$(git status --porcelain)"

cd "$smoke_dir/overlap"
python3 - "$layout" <<'PY'
from pathlib import Path
import sys

layout = Path(sys.argv[1])
layout.write_text(layout.read_text().replace('<nav class="site-nav">', '<nav class="my-nav">'))
PY
commit_all "Customize the navigation"
if "$repoman" update . --vcs-ref v1.1.0 --conflict inline > "$smoke_dir/conflict.log"; then
    echo "Expected an update conflict" >&2
    exit 1
fi
grep -F 'Resolve template update conflicts' "$smoke_dir/conflict.log"
grep -F "$layout" "$smoke_dir/conflict.log"
grep -F '<<<<<<< before updating' "$layout"
grep -F 'class="my-nav"' "$layout"
grep -F 'aria-label="Site"' "$layout"
grep -F '>>>>>>> after updating' "$layout"
test "$(git diff --name-only --diff-filter=U)" = "$layout"
python3 - "$layout" <<'PY'
from pathlib import Path
import re
import sys

layout = Path(sys.argv[1])
resolved, count = re.subn(
    r"^<<<<<<< before updating\n.*?^>>>>>>> after updating\n",
    '    <nav class="my-nav" aria-label="Site">\n',
    layout.read_text(),
    flags=re.MULTILINE | re.DOTALL,
)
assert count == 1
layout.write_text(resolved)
PY
commit_all "Resolve navigation conflict"
npm ci --prefer-offline
npm run check
npm run build
grep -qF 'class="my-nav" aria-label="Site"' dist/index.html
