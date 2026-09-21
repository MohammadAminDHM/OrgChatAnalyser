# OrgChat Check

یک CLI سبک برای اینکه قبل از ساخت یا تحویل چت‌بات سازمانی بفهمیم پروژه در چه وضعیتی است.

دستور اصلی:

```bash
orgchat check
```

## شروع سریع (Quick Start)

نیازمندی‌ها:
- Node.js 16+
- Python 3.11+

سپس:

```bash
cd your-chatbot
npx orgchat check
```

بدون کلون. بدون نصب سراسری OrgChat. بدون ساخت `orgchat.toml` الزامی.

`orgchat init` فقط برای تنظیمات پیشرفته و صریح است.

این دستور هفت سؤال مهم را بررسی می‌کند:

1. داده‌ها کجا هستند و چطور به‌روز می‌شوند؟
2. هر کاربر به چه اطلاعاتی دسترسی دارد؟
3. پاسخ درست را چطور اندازه می‌گیریم؟
4. اگر مدل جواب را نداند چه می‌کند؟
5. هزینه و latency را چطور می‌بینیم؟
6. وقتی سیستم خراب شد چه کسی آن را برمی‌گرداند؟
7. بعد از تحویل چه کسی سیستم را نگهداری می‌کند؟

## نصب محلی

Python 3.11 یا بالاتر لازم است.

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate       # Windows PowerShell
pip install -e .
```

## اجرای بدون کلون (PyPI / uvx)

بدون نصب محلی یا کلون کردن کد:

```bash
uvx orgchat check --config ./orgchat.toml
# یا نصب سراسری
pip install orgchat
orgchat check
```

## تنظیمات پیشرفته (Advanced Configuration)

تنظیمات صریح (اختیاری):

```bash
orgchat init
```

مقادیر `orgchat.toml` را پر کن و بعد:

```bash
orgchat check
```

برای خروجی فایل:

```bash
orgchat check --format markdown --output orgchat-report.md
orgchat check --format json --output orgchat-report.json
```

برای بررسی یک مسیر دیگر:

```bash
orgchat check --path ./my-chatbot
```

برای CI:

```bash
orgchat check --strict
```

کد خروجی:

- `0`: همهٔ کنترل‌ها عبور کرده‌اند یا فقط هشدار غیرstrict وجود دارد.
- `1`: حداقل یک کنترل fail شده، یا در حالت `--strict` هشدار وجود دارد.
- `2`: خطای ورودی، مسیر یا تنظیمات.

## منطق گزارش

`orgchat.toml` منبع اصلی ارزیابی است. مقدارهای صریح `false` یا مسیرهای اشتباه باعث `FAIL` می‌شوند. مقدارهای ثبت‌نشده `WARN` می‌گیرند. CLI در کنار تنظیمات، نام فایل‌ها و پوشه‌های رایج مثل `evals`، `retrieval`، `monitoring` و `runbook` را هم به‌عنوان شواهد کمکی پیدا می‌کند.

شواهد کشف‌شده به‌تنهایی جایگزین تنظیم صریح کنترل‌ها نیستند؛ هدفشان این است که گزارش اولیه از پروژهٔ موجود مفید باشد و مسیر تکمیل را نشان بدهد.

## نمونه خروجی

```text
ORGCHAT CHECK
Project: Enterprise Support Chatbot
Overall: WARN | Score: 64.5/100

Checks:
  [PASS] 100.0/100  داده و به‌روزبودن
  [WARN]  55.0/100  ارزیابی کیفیت
  [FAIL]  40.0/100  دسترسی و امنیت

Next actions:
  1. دسترسی و امنیت: بازیابی را با مجوزهای همان کاربر فیلتر کن.
```

## ساختار پروژه

```text
src/orgchat/
  checker.py    # منطق هفت کنترل
  config.py     # خواندن TOML و مسیرها
  report.py     # خروجی terminal/json/markdown
  cli.py        # دستورات orgchat check و orgchat init
tests/
examples/
```

این نسخه وضعیت آمادگی عملیاتی را گزارش می‌کند و جایگزین تست امنیتی، ارزیابی مدل یا ممیزی سازمانی کامل نیست.
