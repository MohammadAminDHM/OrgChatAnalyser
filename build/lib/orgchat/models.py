from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Finding:
    key: str
    label: str
    status: str
    points: float
    max_points: float
    message: str
    recommendation: str
    evidence: list[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        if not self.max_points:
            return 0.0
        return round((self.points / self.max_points) * 100, 1)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["percentage"] = self.percentage
        return value


@dataclass
class CheckResult:
    key: str
    title: str
    question: str
    status: str
    score: float
    max_score: float
    findings: list[Finding] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["findings"] = [finding.to_dict() for finding in self.findings]
        value["percentage"] = round((self.score / self.max_score) * 100, 1) if self.max_score else 0.0
        return value


@dataclass
class Report:
    project: str
    root: str
    config_file: str | None
    config_loaded: bool
    generated_at: str
    overall_status: str
    score: float
    analysis: str
    checks: list[CheckResult]
    next_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "root": self.root,
            "config_file": self.config_file,
            "config_loaded": self.config_loaded,
            "generated_at": self.generated_at,
            "overall_status": self.overall_status,
            "score": self.score,
            "analysis": self.analysis,
            "checks": [check.to_dict() for check in self.checks],
            "next_actions": self.next_actions,
        }
