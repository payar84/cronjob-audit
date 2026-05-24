"""Diff two sets of cron entries to detect additions, removals, and changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiffEntry:
    """Represents a single change between two snapshots of cron entries."""

    service: str
    name: str
    change_type: str  # 'added' | 'removed' | 'modified'
    old_schedule: Optional[str] = None
    new_schedule: Optional[str] = None
    old_command: Optional[str] = None
    new_command: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "service": self.service,
            "name": self.name,
            "change_type": self.change_type,
            "old_schedule": self.old_schedule,
            "new_schedule": self.new_schedule,
            "old_command": self.old_command,
            "new_command": self.new_command,
        }


@dataclass
class DiffResult:
    """Aggregated diff between two entry snapshots."""

    added: List[DiffEntry] = field(default_factory=list)
    removed: List[DiffEntry] = field(default_factory=list)
    modified: List[DiffEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    def all_changes(self) -> List[DiffEntry]:
        return self.added + self.removed + self.modified

    def to_dict(self) -> Dict:
        return {
            "added": [e.to_dict() for e in self.added],
            "removed": [e.to_dict() for e in self.removed],
            "modified": [e.to_dict() for e in self.modified],
            "summary": {
                "added": len(self.added),
                "removed": len(self.removed),
                "modified": len(self.modified),
            },
        }


def _entry_key(entry: Dict) -> str:
    """Unique key for an entry based on service and name."""
    return f"{entry.get('service', '')}::{entry.get('name', '')}"


def diff_entries(old: List[Dict], new: List[Dict]) -> DiffResult:
    """Compare two lists of raw entry dicts and return a DiffResult."""
    old_map = {_entry_key(e): e for e in old}
    new_map = {_entry_key(e): e for e in new}

    result = DiffResult()

    for key, new_entry in new_map.items():
        if key not in old_map:
            result.added.append(
                DiffEntry(
                    service=new_entry.get("service", ""),
                    name=new_entry.get("name", ""),
                    change_type="added",
                    new_schedule=new_entry.get("schedule"),
                    new_command=new_entry.get("command"),
                )
            )
        else:
            old_entry = old_map[key]
            schedule_changed = old_entry.get("schedule") != new_entry.get("schedule")
            command_changed = old_entry.get("command") != new_entry.get("command")
            if schedule_changed or command_changed:
                result.modified.append(
                    DiffEntry(
                        service=new_entry.get("service", ""),
                        name=new_entry.get("name", ""),
                        change_type="modified",
                        old_schedule=old_entry.get("schedule"),
                        new_schedule=new_entry.get("schedule"),
                        old_command=old_entry.get("command"),
                        new_command=new_entry.get("command"),
                    )
                )

    for key, old_entry in old_map.items():
        if key not in new_map:
            result.removed.append(
                DiffEntry(
                    service=old_entry.get("service", ""),
                    name=old_entry.get("name", ""),
                    change_type="removed",
                    old_schedule=old_entry.get("schedule"),
                    old_command=old_entry.get("command"),
                )
            )

    return result
