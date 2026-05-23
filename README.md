# cronjob-audit

> Python library to parse, validate, and document cron schedules across multiple services into a unified report.

---

## Installation

```bash
pip install cronjob-audit
```

---

## Usage

```python
from cronjob_audit import CronAuditor

auditor = CronAuditor()

# Add cron schedules from multiple services
auditor.add("backup-service", "0 2 * * *", description="Nightly database backup")
auditor.add("email-digest", "30 8 * * 1-5", description="Weekday morning digest")
auditor.add("cache-clear", "*/15 * * * *", description="Clear cache every 15 minutes")

# Validate all schedules
results = auditor.validate()
print(results.summary())

# Export unified report
auditor.export("cron_report.html", format="html")
```

**Example output:**

```
✔ backup-service   → 0 2 * * *       Valid  | Next: 2024-11-01 02:00:00
✔ email-digest     → 30 8 * * 1-5    Valid  | Next: 2024-11-01 08:30:00
✔ cache-clear      → */15 * * * *    Valid  | Next: 2024-11-01 00:15:00

3 schedules audited. 3 valid, 0 invalid.
```

---

## Features

- Parse and validate standard cron expressions
- Aggregate schedules from multiple services into one place
- Detect conflicts, overlaps, and invalid expressions
- Export reports as HTML, JSON, or plain text

---

## License

This project is licensed under the [MIT License](LICENSE).