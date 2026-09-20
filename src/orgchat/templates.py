CONFIG_TEMPLATE = '''# OrgChat readiness configuration
# Run `orgchat check` from the project root after filling these values.

[project]
name = "My organization chatbot"
environment = "staging"

[data_sources]
sources = []
freshness_slo_minutes = 1440
sync_monitoring = false
owner = ""
refresh_test = false

[access_control]
auth = ""
rbac = false
document_level_filters = false
audit_log = false
secret_scan = false

[quality]
eval_dataset = "evals/golden.jsonl"
automated_eval = false
regression_gate = false
min_score = 0.8
last_evaluation = ""

[grounding]
citations = false
abstention = false
fallback = false
prompt_injection_defense = false
retrieval_logging = false

[observability]
tracing = false
token_cost_tracking = false
request_metrics = false
latency_slo_ms = 2000
dashboard = "ops/dashboard.json"

[monitoring]
healthcheck = "/health"
error_logging = false
alerts = false
backup_restore_test = false
incident_runbook = "docs/incident-runbook.md"

[ownership]
service_owner = ""
technical_owner = ""
oncall = ""
runbook = "docs/runbook.md"
review_cadence = "monthly"
'''
