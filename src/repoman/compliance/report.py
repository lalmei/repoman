"""Render compliance reports in multiple formats."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from repoman.compliance.models import ComplianceReport

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Compliance Report</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; background: #111827; color: #e5e7eb; }
    h1, h2, h3 { color: #f9fafb; }
    .meta, .disclaimer { color: #9ca3af; margin-bottom: 1rem; }
    .card { background: #1f2937; border: 1px solid #374151; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; }
    .pill { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 999px; background: #374151; }
    .met { color: #86efac; }
    .unmet { color: #fca5a5; }
    .unknown { color: #fcd34d; }
    .waived { color: #93c5fd; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { padding: 0.5rem; text-align: left; border-bottom: 1px solid #374151; vertical-align: top; }
    th { background: #111827; }
    code { background: #111827; padding: 0.1rem 0.3rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Compliance Report</h1>
  $body
</body>
</html>
"""


def reports_to_json(reports: list[ComplianceReport]) -> str:
    """Render reports as JSON."""
    return json.dumps([report.to_dict() for report in reports], indent=2)


def reports_to_markdown(reports: list[ComplianceReport]) -> str:
    """Render reports as markdown."""
    parts = ["# Compliance Report", ""]
    for report in reports:
        parts.extend(
            [
                f"## {report.profile_title}",
                "",
                f"- Profile: `{report.profile_id}`",
                f"- Repository: `{report.repo_path}`",
                f"- Achieved tier: `{report.achieved_tier or 'none'}`",
                f"- Next tier: `{report.next_tier or 'n/a'}`",
                f"- Requested tier: `{report.requested_tier or 'n/a'}`",
                f"- Gate passed: `{report.gate.passed}`",
                f"- Disclaimer: {report.disclaimer}",
                "",
                "### Summary",
                "",
                f"- Met: {report.summary_counts['met']}",
                f"- Waived: {report.summary_counts['waived']}",
                f"- Unknown: {report.summary_counts['unknown']}",
                f"- Unmet: {report.summary_counts['unmet']}",
                "",
                "### Blockers",
                "",
            ]
        )
        if report.blocking_controls:
            parts.extend(f"- `{control_id}`" for control_id in report.blocking_controls)
        else:
            parts.append("- None")
        parts.extend(["", "### Controls", ""])
        for control in report.controls:
            parts.extend(
                [
                    f"- [{control.status}] `{control.control_id}` ({control.tier}) {control.title}",
                    f"  Evidence: {'; '.join(control.evidence) if control.evidence else 'None recorded'}",
                ]
            )
            if control.justification:
                parts.append(f"  Justification: {control.justification}")
        parts.append("")
    return "\n".join(parts)


def reports_to_html(reports: list[ComplianceReport]) -> str:
    """Render reports as HTML."""
    cards: list[str] = []
    for report in reports:
        summary_html = (
            f"<div class='summary'>"
            f"<div class='card'><strong>Achieved tier</strong><br>{escape(report.achieved_tier or 'none')}</div>"
            f"<div class='card'><strong>Next tier</strong><br>{escape(report.next_tier or 'n/a')}</div>"
            f"<div class='card'><strong>Requested tier</strong><br>{escape(report.requested_tier or 'n/a')}</div>"
            f"<div class='card'><strong>Gate passed</strong><br>{escape(str(report.gate.passed))}</div>"
            f"</div>"
        )
        rows = []
        for control in report.controls:
            rows.append(
                "<tr>"
                f"<td><code>{escape(control.control_id)}</code></td>"
                f"<td>{escape(control.section)}</td>"
                f"<td>{escape(control.tier)}</td>"
                f"<td class='{escape(control.status)}'>{escape(control.status)}</td>"
                f"<td>{escape('; '.join(control.evidence) if control.evidence else 'None recorded')}</td>"
                f"<td>{escape(control.justification or '')}</td>"
                "</tr>"
            )
        cards.append(
            "<section class='card'>"
            f"<h2>{escape(report.profile_title)}</h2>"
            f"<div class='meta'>Profile <code>{escape(report.profile_id)}</code> | Repository: {escape(report.repo_path)}</div>"
            f"<div class='disclaimer'>{escape(report.disclaimer)}</div>"
            f"{summary_html}"
            "<table>"
            "<thead><tr><th>Control</th><th>Section</th><th>Tier</th><th>Status</th><th>Evidence</th><th>Justification</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            "</table>"
            "</section>"
        )
    return HTML_TEMPLATE.replace("$body", "".join(cards))


def write_reports(reports: list[ComplianceReport], output_format: str, output_path: Path) -> Path:
    """Write reports to disk for json, markdown, or html output."""
    output_path = output_path.resolve()
    if output_format == "html":
        output_path.mkdir(parents=True, exist_ok=True)
        target = output_path / "index.html"
        target.write_text(reports_to_html(reports), encoding="utf-8")
        return target

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "json":
        output_path.write_text(reports_to_json(reports), encoding="utf-8")
    elif output_format == "markdown":
        output_path.write_text(reports_to_markdown(reports), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
    return output_path


def build_starter_config(profile_ids: list[str], manual_controls: dict[str, list]) -> str:
    """Build a starter compliance.yml focused on manual controls."""
    lines = [
        "version: 1",
        "profiles:",
    ]
    for profile_id in profile_ids:
        lines.extend(
            [
                f"  {profile_id}:",
                "    enabled: true",
                "    tier_target: null",
                "    include: []",
                "    exclude: []",
            ]
        )
    lines.extend(["defaults: {}", "controls:"])

    any_controls = False
    for profile_id in profile_ids:
        for control in manual_controls.get(profile_id, []):
            any_controls = True
            lines.extend(
                [
                    f"  {control.control_id}:",
                    "    # status: met | unmet | unknown | waived",
                    "    status: unknown",
                    "    justification: null",
                    "    owner: null",
                    "    evidence: []",
                    "    last_reviewed: null",
                    f'    notes: "{control.title}: {control.description}"',
                ]
            )
    if not any_controls:
        lines.append("  {}")
    return "\n".join(lines) + "\n"
