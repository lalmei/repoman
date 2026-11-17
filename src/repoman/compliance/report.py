"""Render compliance reports in multiple formats."""

from __future__ import annotations

import json
from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from repoman.compliance.models import ComplianceReport, ControlDefinition

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
                f"- Not applicable: {report.summary_counts.get('not_applicable', 0)}",
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
            f"<div class='card'><strong>Not applicable</strong><br>{escape(str(report.summary_counts.get('not_applicable', 0)))}</div>"
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
                f"<td>{escape(', '.join(control.criteria_refs) or '-')}</td>"
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
            "<thead><tr><th>Control</th><th>Section</th><th>Tier</th><th>Status</th><th>Criteria</th><th>Evidence</th><th>Justification</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            "</table>"
            "</section>"
        )
    return HTML_TEMPLATE.replace("$body", "".join(cards))


def reports_to_evidence_markdown(reports: list[ComplianceReport]) -> str:
    """Render SOC 2 repository audit evidence reports as markdown."""
    parts = ["# SOC 2 Repository Audit Evidence Report", ""]
    for report in reports:
        metadata = report.report_metadata
        parts.extend(
            [
                f"## {report.profile_title}",
                "",
                f"- Profile: `{report.profile_id}`",
                f"- Repository: `{metadata.repository_url or report.repo_path}`",
                f"- Organization: `{metadata.organization or 'not recorded'}`",
                f"- System: `{metadata.system_name or 'not recorded'}`",
                f"- Audit period: `{metadata.audit_period_start or 'not recorded'}` to `{metadata.audit_period_end or 'not recorded'}`",
                f"- Prepared by: `{metadata.prepared_by or 'not recorded'}`",
                f"- Generated at: `{report.generated_at}`",
                f"- Disclaimer: {report.disclaimer}",
                "",
                "### Scope",
                "",
                metadata.scope_summary or "No scope summary recorded.",
                "",
                "### Summary",
                "",
                f"- Requested tier: `{report.requested_tier or 'n/a'}`",
                f"- Achieved tier: `{report.achieved_tier or 'none'}`",
                f"- Gate passed: `{report.gate.passed}`",
                f"- Met: {report.summary_counts['met']}",
                f"- Waived: {report.summary_counts['waived']}",
                f"- Not applicable: {report.summary_counts.get('not_applicable', 0)}",
                f"- Unknown: {report.summary_counts['unknown']}",
                f"- Unmet: {report.summary_counts['unmet']}",
                "",
            ]
        )
        parts.extend(_provider_markdown(report))
        parts.extend(_manual_completion_markdown(report))
        parts.extend(["### Control Evidence", ""])
        for control in report.controls:
            parts.extend(
                [
                    f"#### `{control.control_id}` — {control.title}",
                    "",
                    f"- Status: `{control.status}`",
                    f"- Tier: `{control.tier}`",
                    f"- Section: `{control.section}`",
                    f"- SOC 2 criteria: `{', '.join(control.criteria_refs) or 'not mapped'}`",
                    f"- Required evidence: {control.required_evidence or 'Not specified'}",
                    f"- Owner: `{control.owner or 'not recorded'}`",
                    f"- Last reviewed: `{control.last_reviewed or 'not recorded'}`",
                    f"- Detection: `{control.detection_kind}`",
                    f"- Evidence: {'; '.join(control.evidence) if control.evidence else 'None recorded'}",
                ]
            )
            if control.justification:
                parts.append(f"- Justification: {control.justification}")
            if control.notes:
                parts.append(f"- Notes: {control.notes}")
            parts.append("")
    return "\n".join(parts)


def reports_to_evidence_html(reports: list[ComplianceReport]) -> str:
    """Render SOC 2 repository audit evidence reports as HTML."""
    body = reports_to_evidence_markdown(reports)
    rows = "".join(f"<pre>{escape(section)}</pre>" for section in body.split("\n\n") if section.strip())
    return HTML_TEMPLATE.replace(
        "<title>Compliance Report</title>",
        "<title>SOC 2 Repository Audit Evidence Report</title>",
    ).replace(
        "<h1>Compliance Report</h1>\n  $body",
        f"<h1>SOC 2 Repository Audit Evidence Report</h1>\n  {rows}",
    )


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


def write_evidence_reports(reports: list[ComplianceReport], output_format: str, output_path: Path) -> Path:
    """Write evidence reports to disk for json, markdown, or html output."""
    output_path = output_path.resolve()
    if output_format == "html":
        output_path.mkdir(parents=True, exist_ok=True)
        target = output_path / "index.html"
        target.write_text(reports_to_evidence_html(reports), encoding="utf-8")
        return target

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "json":
        output_path.write_text(reports_to_json(reports), encoding="utf-8")
    elif output_format == "markdown":
        output_path.write_text(reports_to_evidence_markdown(reports), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
    return output_path


def build_starter_config(profile_ids: list[str], controls_by_profile: dict[str, list[ControlDefinition]]) -> str:
    """Build a starter compliance.yml for manual and hybrid evidence."""
    lines = [
        "version: 1",
        "report:",
        "  organization: null",
        "  system_name: null",
        "  audit_period_start: null",
        "  audit_period_end: null",
        "  prepared_by: null",
        "  repository_url: null",
        "  scope_summary: null",
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
        for control in controls_by_profile.get(profile_id, []):
            any_controls = True
            lines.extend(
                [
                    f"  {control.control_id}:",
                    f"    # detection: {control.detection.kind}",
                    f"    # criteria: {', '.join(control.criteria_refs) or 'not mapped'}",
                    f"    # required_evidence: {control.required_evidence or 'not specified'}",
                    "    # status: met | unmet | unknown | waived | not_applicable",
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


def _provider_markdown(report: ComplianceReport) -> list[str]:
    provider = report.provider_evidence
    if provider is None:
        return [
            "### Provider Evidence",
            "",
            "- Provider evidence was not collected.",
            "",
        ]

    lines = [
        "### Provider Evidence",
        "",
        f"- Provider: `{provider.provider or 'not detected'}`",
        f"- Repository: `{provider.repository or 'not detected'}`",
        f"- Available: `{provider.available}`",
        f"- Collected at: `{provider.collected_at or 'not recorded'}`",
    ]
    if provider.warnings:
        lines.extend(f"- Warning: {warning}" for warning in provider.warnings)
    lines.append("")
    return lines


def _manual_completion_markdown(report: ComplianceReport) -> list[str]:
    gaps = [control for control in report.controls if control.status in {"unknown", "unmet"}]
    lines = ["### Manual Completion Required", ""]
    if not gaps:
        lines.extend(["- None", ""])
        return lines
    for control in gaps:
        lines.extend(
            [
                f"#### `{control.control_id}`",
                "",
                f"- Current status: `{control.status}`",
                f"- Required evidence: {control.required_evidence or 'Not specified'}",
                "```yaml",
                f"  {control.control_id}:",
                "    status: met",
                "    justification: null",
                "    owner: null",
                "    evidence:",
                '      - "Describe the evidence or link to the retained artifact."',
                "    last_reviewed: null",
                "    notes: null",
                "```",
                "",
            ]
        )
    return lines
