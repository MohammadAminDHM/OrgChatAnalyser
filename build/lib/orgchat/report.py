from __future__ import annotations

import json
from typing import Any

from .models import CheckResult, Report


def _status(status: str) -> str:
    return {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}.get(status, status)


def render_terminal(report: Report) -> str:
    lines = [
        "ORGCHAT CHECK",
        f"Project: {report.project}",
        f"Root: {report.root}",
        f"Config: {report.config_file or 'orgchat.toml پیدا نشد'}",
        "",
        f"Overall: {_status(report.overall_status)} | Score: {report.score}/100",
        f"Analysis: {report.analysis}",
        "",
        "Checks:",
    ]
    for check in report.checks:
        lines.append(f"  [{_status(check.status):4}] {check.score:5.1f}/{check.max_score:g}  {check.title}")
        lines.append(f"         {check.question}")
        for finding in check.findings:
            if finding.status != "PASS":
                lines.append(f"         - [{finding.status}] {finding.label}: {finding.message}")
        if check.evidence:
            lines.append(f"         Evidence: {', '.join(check.evidence[:3])}")

    if report.next_actions:
        lines.extend(["", "Next actions:"])
        lines.extend(f"  {index}. {action}" for index, action in enumerate(report.next_actions, start=1))

    lines.extend(["", f"Generated: {report.generated_at}"])
    return "\n".join(lines)


def render_markdown(report: Report) -> str:
    lines = [
        f"# OrgChat Check: {report.project}",
        "",
        f"- وضعیت کلی: **{report.overall_status}**",
        f"- امتیاز: **{report.score}/100**",
        f"- تحلیل: {report.analysis}",
        f"- مسیر پروژه: `{report.root}`",
        f"- تنظیمات: `{report.config_file or 'orgchat.toml پیدا نشد'}`",
        "",
        "## خلاصهٔ بررسی‌ها",
        "",
        "| وضعیت | امتیاز | محور | سؤال اصلی |",
        "|---|---:|---|---|",
    ]
    for check in report.checks:
        lines.append(f"| {check.status} | {check.score:.1f}/{check.max_score:g} | {check.title} | {check.question} |")

    for check in report.checks:
        lines.extend(["", f"## {check.title}", "", f"سؤال: {check.question}", ""])
        for finding in check.findings:
            lines.append(f"- **{finding.status}** {finding.label}: {finding.message}")
            if finding.status != "PASS":
                lines.append(f"  - اقدام: {finding.recommendation}")
        if check.evidence:
            lines.append(f"- شواهد پیدا‌شده: `{', '.join(check.evidence)}`")

    if report.next_actions:
        lines.extend(["", "## اقدام‌های بعدی", ""])
        lines.extend(f"{index}. {action}" for index, action in enumerate(report.next_actions, start=1))
    return "\n".join(lines) + "\n"


def render_json(report: Report) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n"


def render(report: Report, output_format: str) -> str:
    if output_format == "json":
        return render_json(report)
    if output_format == "markdown":
        return render_markdown(report)
    return render_terminal(report)
