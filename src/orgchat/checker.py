from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .config import load_config, resolve_project_path, section
from .models import CheckResult, Finding, Report


@dataclass(frozen=True)
class Signal:
    key: str
    label: str
    kind: str
    points: float
    recommendation: str
    field: str


CHECK_DEFINITIONS: list[dict[str, Any]] = [
    {
        "key": "data_sources",
        "title": "داده و به‌روزبودن",
        "question": "داده‌ها کجا هستند و چطور به‌روز می‌شوند؟",
        "patterns": ["minio", "s3", "storage", "ingest", "sync", "etl", "pipeline", "freshness"],
        "signals": [
            Signal("sources", "منابع داده مشخص شده‌اند", "list", 25, "منبع‌های واقعی مثل MinIO، PostgreSQL یا S3 را در orgchat.toml ثبت کن.", "sources"),
            Signal("freshness_slo_minutes", "حد به‌روزبودن داده مشخص است", "number", 20, "برای داده‌ها یک بازهٔ مجاز تأخیر تعیین کن.", "freshness_slo_minutes"),
            Signal("sync_monitoring", "همگام‌سازی پایش می‌شود", "bool", 20, "برای شکست یا عقب‌افتادن ingestion هشدار تعریف کن.", "sync_monitoring"),
            Signal("owner", "مالک داده مشخص است", "text", 20, "یک مالک مشخص برای صحت و به‌روزبودن داده تعیین کن.", "owner"),
            Signal("refresh_test", "تست تازه‌سازی وجود دارد", "bool", 15, "یک تست قابل‌اجرا برای refresh یا ingestion اضافه کن.", "refresh_test"),
        ],
    },
    {
        "key": "access_control",
        "title": "دسترسی و امنیت",
        "question": "هر کاربر به چه اطلاعاتی دسترسی دارد؟",
        "patterns": ["auth", "rbac", "acl", "permission", "tenant", "jwt", "oidc", "oauth", "audit"],
        "signals": [
            Signal("auth", "احراز هویت فعال است", "text", 20, "یک روش احراز هویت سازمانی مثل OIDC، OAuth یا JWT ثبت کن.", "auth"),
            Signal("rbac", "نقش‌ها و مجوزها تعریف شده‌اند", "bool", 25, "RBAC را برای نقش‌های کاربر، مدیر و اپراتور تعریف کن.", "rbac"),
            Signal("document_level_filters", "فیلتر دسترسی در سطح سند وجود دارد", "bool", 25, "بازیابی را با مجوزهای همان کاربر فیلتر کن.", "document_level_filters"),
            Signal("audit_log", "گزارش دسترسی ثبت می‌شود", "bool", 15, "رویدادهای دسترسی و پاسخ‌های حساس را audit کن.", "audit_log"),
            Signal("secret_scan", "کنترل نشت secrets انجام می‌شود", "bool", 15, "Secret scanning را در مخزن و CI فعال کن.", "secret_scan"),
        ],
    },
    {
        "key": "quality",
        "title": "ارزیابی کیفیت",
        "question": "پاسخ درست را چطور اندازه می‌گیریم؟",
        "patterns": ["eval", "golden", "benchmark", "quality", "regression"],
        "signals": [
            Signal("eval_dataset", "مجموعهٔ ارزیابی وجود دارد", "path", 25, "یک golden dataset واقعی از سؤال‌ها و پاسخ‌های مورد انتظار بساز.", "eval_dataset"),
            Signal("automated_eval", "ارزیابی خودکار اجرا می‌شود", "bool", 25, "ارزیابی را در CI یا یک job زمان‌بندی‌شده اجرا کن.", "automated_eval"),
            Signal("regression_gate", "گیت جلوگیری از regression وجود دارد", "bool", 20, "اجازهٔ deploy را به عبور از حداقل امتیاز مشروط کن.", "regression_gate"),
            Signal("min_score", "حداقل امتیاز کیفیت تعیین شده", "number", 15, "حداقل امتیاز قابل‌قبول را مشخص کن.", "min_score"),
            Signal("last_evaluation", "ارزیابی اخیر است", "recent", 15, "نتیجهٔ ارزیابی را مرتباً اجرا و تاریخ آخرین اجرا را ثبت کن.", "last_evaluation"),
        ],
    },
    {
        "key": "grounding",
        "title": "پاسخ مستند و fallback",
        "question": "اگر مدل جواب را نداند یا داده کافی نباشد چه می‌کند؟",
        "patterns": ["retrieval", "citation", "source", "fallback", "abstain", "rerank"],
        "signals": [
            Signal("citations", "پاسخ منبع و citation دارد", "bool", 25, "منبع سند و بخش مرتبط را همراه پاسخ نمایش بده.", "citations"),
            Signal("abstention", "مدل می‌تواند از پاسخ‌سازی خودداری کند", "bool", 25, "برای نبود شواهد، پاسخ صادقانهٔ «اطلاعات کافی نیست» تعریف کن.", "abstention"),
            Signal("fallback", "مسیر fallback انسانی یا عملیاتی وجود دارد", "bool", 20, "پاسخ‌های کم‌اطمینان را به اپراتور یا مسیر جایگزین بفرست.", "fallback"),
            Signal("prompt_injection_defense", "دفاع در برابر prompt injection وجود دارد", "bool", 15, "ورودی سند و کاربر را از دستورهای سیستمی جدا و تست کن.", "prompt_injection_defense"),
            Signal("retrieval_logging", "فرایند بازیابی قابل‌ردگیری است", "bool", 15, "سندها، chunkها و score بازیابی‌شده را برای عیب‌یابی ثبت کن.", "retrieval_logging"),
        ],
    },
    {
        "key": "observability",
        "title": "هزینه و مشاهده‌پذیری",
        "question": "هزینه، latency و کیفیت سرویس را چطور می‌بینیم؟",
        "patterns": ["telemetry", "tracing", "metrics", "prometheus", "cost", "token", "latency"],
        "signals": [
            Signal("tracing", "trace هر درخواست وجود دارد", "bool", 20, "برای هر درخواست trace از ورودی تا retrieval و generation بساز.", "tracing"),
            Signal("token_cost_tracking", "هزینهٔ token یا inference ثبت می‌شود", "bool", 25, "هزینه را به پروژه، کاربر یا تیم نسبت بده.", "token_cost_tracking"),
            Signal("request_metrics", "متریک درخواست وجود دارد", "bool", 20, "تعداد درخواست، خطا، latency و نرخ fallback را اندازه بگیر.", "request_metrics"),
            Signal("latency_slo_ms", "SLO پاسخ مشخص است", "number", 15, "یک latency هدف برای پاسخ تعیین کن.", "latency_slo_ms"),
            Signal("dashboard", "داشبورد قابل‌استفاده وجود دارد", "path", 20, "یک داشبورد برای وضعیت و روندهای سرویس نگه‌دار.", "dashboard"),
        ],
    },
    {
        "key": "monitoring",
        "title": "مانیتورینگ و بازیابی",
        "question": "وقتی سیستم خراب شد چه کسی و با چه روشی آن را برمی‌گرداند؟",
        "patterns": ["monitor", "health", "alert", "sentry", "incident", "watchdog", "backup"],
        "signals": [
            Signal("healthcheck", "health check تعریف شده", "text", 20, "یک endpoint یا دستور health check قابل‌اجرا ثبت کن.", "healthcheck"),
            Signal("error_logging", "خطاها ثبت می‌شوند", "bool", 25, "خطاهای backend، retrieval و مدل را با context کافی ذخیره کن.", "error_logging"),
            Signal("alerts", "هشدار عملیاتی وجود دارد", "bool", 20, "برای خطا، latency، هزینه و افت کیفیت alert بساز.", "alerts"),
            Signal("backup_restore_test", "بازیابی تست شده است", "bool", 15, "backup را فقط نگیر؛ restore آن را دوره‌ای تست کن.", "backup_restore_test"),
            Signal("incident_runbook", "راهنمای incident وجود دارد", "path", 20, "برای خرابی مدل، منبع داده و سرویس یک runbook بنویس.", "incident_runbook"),
        ],
    },
    {
        "key": "ownership",
        "title": "مالکیت و نگهداری",
        "question": "بعد از تحویل، چه کسی سیستم را نگهداری می‌کند؟",
        "patterns": ["owner", "maintainer", "runbook", "oncall", "operations", "docs"],
        "signals": [
            Signal("service_owner", "مالک سرویس مشخص است", "text", 25, "یک تیم یا فرد پاسخ‌گو برای سرویس تعیین کن.", "service_owner"),
            Signal("technical_owner", "مالک فنی مشخص است", "text", 20, "مسئول تصمیم‌های فنی و تغییرات معماری را مشخص کن.", "technical_owner"),
            Signal("oncall", "مسیر on-call مشخص است", "text", 20, "برای incident یک مسیر پاسخ‌گویی واقعی تعیین کن.", "oncall"),
            Signal("runbook", "runbook اصلی وجود دارد", "path", 20, "نحوهٔ deploy، rollback، عیب‌یابی و refresh را مستند کن.", "runbook"),
            Signal("review_cadence", "دورهٔ بازبینی مشخص است", "text", 15, "بازبینی ماهانهٔ کیفیت، امنیت و هزینه را در تقویم بگذار.", "review_cadence"),
        ],
    },
]


IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache", "dist", "build"}


def discover_paths(root: Path, limit: int = 6000) -> list[str]:
    paths: list[str] = []
    try:
        iterator = root.rglob("*")
        for path in iterator:
            if len(paths) >= limit:
                break
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            if path.is_file():
                paths.append(path.relative_to(root).as_posix().lower())
    except OSError:
        return paths
    return paths


def _evidence(paths: list[str], patterns: list[str]) -> list[str]:
    matches = []
    for path in paths:
        if path.endswith((".md", ".txt")) and path not in {"readme.md", "readme.txt"}:
            pass
        if any(pattern in path for pattern in patterns):
            matches.append(path)
    return matches[:5]


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "on"}:
            return True
        if normalized in {"false", "no", "0", "off"}:
            return False
    return None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.combine(date.fromisoformat(text), datetime.min.time())
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _assess(
    root: Path,
    values: dict[str, Any],
    signal: Signal,
    evidence: list[str],
) -> tuple[str, float, str]:
    present = signal.field in values
    value = values.get(signal.field)

    if signal.kind == "bool":
        parsed = _as_bool(value)
        if parsed is True:
            return "PASS", signal.points, "فعال است."
        if parsed is False:
            return "FAIL", 0.0, "صراحتاً غیرفعال تنظیم شده است."
        return "WARN", signal.points * 0.35 if evidence else 0.0, "در تنظیمات مشخص نشده است." if not present else "مقدار بولی قابل‌تشخیص نیست."

    if signal.kind == "list":
        if isinstance(value, list) and value:
            return "PASS", signal.points, f"{len(value)} مورد ثبت شده است."
        if present and isinstance(value, list):
            return "FAIL", 0.0, "فهرست خالی است."
        return "WARN", signal.points * 0.35 if evidence else 0.0, "در تنظیمات مشخص نشده است."

    if signal.kind == "text":
        if isinstance(value, str) and value.strip():
            return "PASS", signal.points, "ثبت شده است."
        if present:
            return "FAIL", 0.0, "خالی است."
        return "WARN", signal.points * 0.35 if evidence else 0.0, "در تنظیمات مشخص نشده است."

    if signal.kind == "path":
        path = resolve_project_path(root, value)
        if path and path.exists():
            try:
                display_path = path.relative_to(root).as_posix()
            except ValueError:
                display_path = str(path)
            return "PASS", signal.points, f"فایل پیدا شد: {display_path}"
        if present and isinstance(value, str) and value.strip():
            return "FAIL", 0.0, f"مسیر پیدا نشد: {value}"
        return "WARN", signal.points * 0.35 if evidence else 0.0, "مسیر در تنظیمات مشخص نشده است."

    if signal.kind == "number":
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.0
        if number > 0:
            return "PASS", signal.points, f"مقدار {number:g} ثبت شده است."
        if present:
            return "FAIL", 0.0, "مقدار باید بزرگ‌تر از صفر باشد."
        return "WARN", signal.points * 0.35 if evidence else 0.0, "در تنظیمات مشخص نشده است."

    if signal.kind == "recent":
        parsed = _parse_datetime(value)
        if parsed is None:
            if present and value:
                return "FAIL", 0.0, "تاریخ قابل‌خواندن نیست."
            return "WARN", signal.points * 0.35 if evidence else 0.0, "تاریخ آخرین اجرا ثبت نشده است."
        age = datetime.now(timezone.utc) - parsed
        if age <= timedelta(days=30) and age >= timedelta(days=-1):
            return "PASS", signal.points, f"آخرین اجرا {age.days} روز قبل بوده است."
        return "FAIL", 0.0, f"آخرین اجرا {age.days} روز قبل بوده و stale است."

    return "WARN", 0.0, "نوع بررسی ناشناخته است."


def _evaluate_check(root: Path, config: dict[str, Any], paths: list[str], definition: dict[str, Any], use_heuristics: bool) -> CheckResult:
    values = section(config, definition["key"])
    evidence = _evidence(paths, definition["patterns"]) if use_heuristics else []
    findings: list[Finding] = []

    for signal in definition["signals"]:
        status, points, message = _assess(root, values, signal, evidence)
        findings.append(
            Finding(
                key=signal.key,
                label=signal.label,
                status=status,
                points=round(points, 2),
                max_points=signal.points,
                message=message,
                recommendation=signal.recommendation,
                evidence=evidence[:3] if status != "PASS" else [],
            )
        )

    score = round(sum(finding.points for finding in findings), 2)
    max_score = sum(finding.max_points for finding in findings)
    if any(finding.status == "FAIL" for finding in findings):
        status = "FAIL"
    elif any(finding.status == "WARN" for finding in findings):
        status = "WARN"
    else:
        status = "PASS"

    return CheckResult(
        key=definition["key"],
        title=definition["title"],
        question=definition["question"],
        status=status,
        score=score,
        max_score=max_score,
        findings=findings,
        evidence=evidence,
    )


def build_report(root: str | Path, config_path: str | Path | None = None, use_heuristics: bool = True, context_config: dict | None = None) -> Report:
    project_root = Path(root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        raise ValueError(f"Project path is not a directory: {project_root}")

    requested_config = Path(config_path).expanduser() if config_path else None
    config, loaded_path, loaded = load_config(project_root, requested_config)
    if context_config:
        for k, v in context_config.items():
            if isinstance(v, dict) and k in config and isinstance(config[k], dict):
                config[k].update(v)
            else:
                config[k] = v
    paths = discover_paths(project_root) if use_heuristics else []
    checks = [_evaluate_check(project_root, config, paths, definition, use_heuristics) for definition in CHECK_DEFINITIONS]

    total = sum(check.score for check in checks)
    maximum = sum(check.max_score for check in checks)
    score = round((total / maximum) * 100, 1) if maximum else 0.0
    if any(check.status == "FAIL" for check in checks):
        overall_status = "FAIL"
    elif any(check.status == "WARN" for check in checks):
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    failed = sum(check.status == "FAIL" for check in checks)
    warned = sum(check.status == "WARN" for check in checks)
    if overall_status == "PASS":
        analysis = "هر هفت محور اصلی کنترل شده‌اند و شواهد لازم در تنظیمات پروژه ثبت شده است."
    elif overall_status == "FAIL":
        analysis = f"پروژه هنوز آمادهٔ تحویل سازمانی نیست؛ {failed} محور دارای شکاف جدی و {warned} محور نیازمند تکمیل است."
    elif not loaded:
        analysis = "فایل orgchat.toml پیدا نشد؛ این گزارش فقط یک baseline اولیه است و برای ارزیابی واقعی باید تنظیمات پروژه ثبت شود."
    else:
        analysis = f"پروژه در وضعیت میانی است؛ {warned} محور نیازمند تکمیل است و هنوز FAIL جدی ثبت نشده."

    actions: list[str] = []
    for check in checks:
        for finding in check.findings:
            if finding.status != "PASS":
                actions.append(f"{check.title}: {finding.recommendation}")
    actions = actions[:8]

    project_section = section(config, "project")
    project_name = project_section.get("name") if isinstance(project_section.get("name"), str) else project_root.name
    config_display = None
    if loaded_path:
        try:
            config_display = loaded_path.relative_to(project_root).as_posix()
        except ValueError:
            config_display = str(loaded_path)

    return Report(
        project=project_name or project_root.name,
        root=str(project_root),
        config_file=config_display,
        config_loaded=loaded,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        overall_status=overall_status,
        score=score,
        analysis=analysis,
        checks=checks,
        next_actions=actions,
    )
