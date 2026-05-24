"""Load cron job definitions from YAML or JSON config files."""

import json
from pathlib import Path
from typing import List

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


class LoaderError(Exception):
    """Raised when a config file cannot be loaded or parsed."""


def _load_raw(path: Path) -> dict:
    suffix = path.suffix.lower()
    with path.open("r", encoding="utf-8") as fh:
        if suffix in (".yaml", ".yml"):
            if not _YAML_AVAILABLE:
                raise LoaderError("PyYAML is required to load .yaml files: pip install pyyaml")
            return yaml.safe_load(fh)
        elif suffix == ".json":
            return json.load(fh)
        else:
            raise LoaderError(f"Unsupported file format: {suffix!r}")


def _validate_job(job: object, index: int) -> None:
    """Validate a single job entry, raising LoaderError with a useful message on failure."""
    if not isinstance(job, dict):
        raise LoaderError(f"Job at index {index} must be a mapping, got: {type(job).__name__}")
    if "schedule" not in job:
        name = job.get("name", f"<index {index}>")
        raise LoaderError(f"Job {name!r} is missing required field 'schedule'")


def load_entries(path: str) -> List[dict]:
    """Load cron entries from a YAML or JSON file.

    Expected structure::

        service: my-service
        jobs:
          - name: cleanup
            schedule: "0 2 * * *"
          - name: report
            schedule: "*/15 * * * *"
    """
    resolved = Path(path)
    if not resolved.exists():
        raise LoaderError(f"Config file not found: {path}")

    raw = _load_raw(resolved)
    if not isinstance(raw, dict):
        raise LoaderError("Config file must be a mapping at the top level")

    service = raw.get("service", resolved.stem)
    jobs = raw.get("jobs", [])
    if not isinstance(jobs, list):
        raise LoaderError("'jobs' must be a list")

    entries = []
    for index, job in enumerate(jobs):
        _validate_job(job, index)
        entries.append({
            "service": service,
            "name": job.get("name", "unnamed"),
            "schedule": job.get("schedule", ""),
        })
    return entries
