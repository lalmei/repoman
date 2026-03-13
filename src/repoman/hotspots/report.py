"""HTML report generation for hotspot analysis.

Pure logic module: no Typer, Rich, or CLI imports. Writes HTML files.
"""

from datetime import datetime
from html import escape
from pathlib import Path

from repoman.hotspots.analysis import HotspotResult

# Severity percentile thresholds: top 20% = high, next 30% = medium, rest = low
_HOT_HIGH_THRESHOLD = 0.2
_HOT_MEDIUM_THRESHOLD = 0.5

_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Hotspot Report</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2em; background: #1e1e1e; color: #d4d4d4; }
    h1 { font-size: 1.5em; margin-bottom: 0.5em; }
    .meta { color: #888; font-size: 0.9em; margin-bottom: 1.5em; }
    table { border-collapse: collapse; width: 100%; }
    th, td { padding: 0.5em 1em; text-align: left; border-bottom: 1px solid #333; }
    th { background: #2d2d2d; font-weight: 600; }
    td.num { text-align: right; }
    a { color: #569cd6; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .hot-high { background: rgba(255, 80, 80, 0.15); }
    .hot-medium { background: rgba(255, 165, 0, 0.15); }
    .hot-low { background: rgba(100, 200, 100, 0.1); }
  </style>
</head>
<body>
  <h1>Hotspot Report</h1>
  <div class="meta">
    <span>Repository: $repo_path</span>
    $date_range
  </div>
  <table>
    <thead>
      <tr><th>File</th><th class="num">Commits</th><th class="num">Churn</th><th class="num">Contributors</th><th class="num">Score</th></tr>
    </thead>
    <tbody>
      $rows
    </tbody>
  </table>
</body>
</html>
"""

_FILE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>$file_path - Hotspot</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2em; background: #1e1e1e; color: #d4d4d4; }
    .banner { background: #2d2d2d; padding: 1em; border-radius: 4px; margin-bottom: 1em; }
    .banner .path { font-weight: 600; margin-bottom: 0.5em; }
    .banner .metrics { font-size: 0.9em; color: #888; }
    .banner .badge { display: inline-block; padding: 0.2em 0.5em; border-radius: 3px; font-size: 0.85em; margin-left: 0.5em; }
    .badge-high { background: rgba(255, 80, 80, 0.5); }
    .badge-medium { background: rgba(255, 165, 0, 0.5); }
    .badge-low { background: rgba(100, 200, 100, 0.3); }
    a { color: #569cd6; text-decoration: none; }
    a:hover { text-decoration: underline; }
    pre { margin: 0; overflow-x: auto; background: #252526; padding: 1em; border-radius: 4px; }
    .source { font-family: monospace; font-size: 13px; line-height: 1.5; }
    .line { white-space: pre; }
    .line-num { display: inline-block; width: 3em; color: #858585; user-select: none; }
    .line.hot-line-high { background: rgba(255, 80, 80, 0.2); }
  </style>
</head>
<body>
  <div class="banner">
    <div class="path">$file_path <span class="badge $badge_class">$severity_label</span></div>
    <div class="metrics">Commits: $commits_count | Churn: $code_churn | Contributors: $contributors_count | Score: $score</div>
  </div>
  <p><a href="index.html">&larr; Back to index</a></p>
  <pre class="source">$source_html</pre>
</body>
</html>
"""


def _path_to_filename(file_path: str) -> str:
    """Convert file path to safe HTML filename."""
    safe = file_path.replace("\\", "_").replace("/", "_")
    return f"{safe}.html"


def _severity_class(rank: float) -> str:
    """Return CSS class from rank 0-1 (0=highest score)."""
    if rank < _HOT_HIGH_THRESHOLD:
        return "hot-high"
    if rank < _HOT_MEDIUM_THRESHOLD:
        return "hot-medium"
    return "hot-low"


def _badge_class(rank: float) -> str:
    """Return badge CSS class for file banner."""
    if rank < _HOT_HIGH_THRESHOLD:
        return "badge-high"
    if rank < _HOT_MEDIUM_THRESHOLD:
        return "badge-medium"
    return "badge-low"


def _severity_label(rank: float) -> str:
    """Return human-readable severity label."""
    if rank < _HOT_HIGH_THRESHOLD:
        return "high"
    if rank < _HOT_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def generate_report(
    results: list[HotspotResult],
    repo_path: Path,
    output_dir: Path,
    *,
    since: datetime | None = None,
    to: datetime | None = None,
) -> None:
    """Generate an HTML hotspot report.

    Writes index.html and per-file HTML pages. Skips files that cannot be read.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_path = repo_path.resolve()

    scores = [r.score for r in results]
    max_score = max(scores) if scores else 1.0
    min_score = min(scores) if scores else 0.0
    score_range = max_score - min_score if max_score != min_score else 1.0

    def rank_for(r: HotspotResult) -> float:
        return (max_score - r.score) / score_range if score_range else 0.0

    date_range_html = ""
    if since is not None or to is not None:
        parts = []
        if since is not None:
            parts.append(f"Since: {since.strftime('%Y-%m-%d')}")
        if to is not None:
            parts.append(f"To: {to.strftime('%Y-%m-%d')}")
        date_range_html = f" | {' | '.join(parts)}"

    rows_html_parts: list[str] = []
    for r in results:
        rank = rank_for(r)
        severity = _severity_class(rank)
        filename = _path_to_filename(r.file_path)
        rows_html_parts.append(
            f'<tr class="{severity}">'
            f'<td><a href="{escape(filename)}">{escape(r.file_path)}</a></td>'
            f'<td class="num">{r.commits_count}</td>'
            f'<td class="num">{r.code_churn}</td>'
            f'<td class="num">{r.contributors_count}</td>'
            f'<td class="num">{r.score:.1f}</td>'
            "</tr>"
        )

    index_html = _INDEX_TEMPLATE.replace("$repo_path", escape(str(repo_path)))
    index_html = index_html.replace("$date_range", date_range_html)
    index_html = index_html.replace("$rows", "\n      ".join(rows_html_parts))

    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    for r in results:
        rank = rank_for(r)
        badge_class = _badge_class(rank)
        severity_label = _severity_label(rank)
        file_full_path = repo_path / r.file_path

        try:
            source = file_full_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            continue

        lines_data: list[dict] = []
        for num, content in enumerate(source.splitlines(), start=1):
            lines_data.append({"num": num, "content": content, "highlight_class": None})

        source_lines_html = "\n".join(
            f'<span class="line"><span class="line-num">{ln["num"]}</span>{escape(ln["content"]) or " "}</span>'
            for ln in lines_data
        )
        source_html = source_lines_html

        file_html = _FILE_TEMPLATE.replace("$file_path", escape(r.file_path))
        file_html = file_html.replace("$badge_class", badge_class)
        file_html = file_html.replace("$severity_label", severity_label)
        file_html = file_html.replace("$commits_count", str(r.commits_count))
        file_html = file_html.replace("$code_churn", str(r.code_churn))
        file_html = file_html.replace("$contributors_count", str(r.contributors_count))
        file_html = file_html.replace("$score", f"{r.score:.1f}")
        file_html = file_html.replace("$source_html", source_html)

        (output_dir / _path_to_filename(r.file_path)).write_text(file_html, encoding="utf-8")
