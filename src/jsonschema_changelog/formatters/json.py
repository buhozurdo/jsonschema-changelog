"""JSON formatter for changelogs."""

import json
from typing import Any, Dict

from jsonschema_changelog.changelog import Changelog


class JsonFormatter:
    """Format changelog as JSON.

    Generates a structured JSON representation of the changelog
    suitable for programmatic consumption.

    Example:
        >>> formatter = JsonFormatter()
        >>> json_output = formatter.format(changelog)

    """

    def __init__(
        self,
        indent: int = 2,
        sort_keys: bool = False,
        include_metadata: bool = True,
    ) -> None:
        """Initialize JsonFormatter.

        Args:
            indent: JSON indentation level
            sort_keys: Whether to sort dictionary keys
            include_metadata: Include metadata in output

        """
        self.indent = indent
        self.sort_keys = sort_keys
        self.include_metadata = include_metadata

    def format(self, changelog: Changelog) -> str:
        """Format a changelog as JSON.

        Args:
            changelog: The changelog to format

        Returns:
            JSON formatted string

        """
        data = self._to_dict(changelog)
        return json.dumps(
            data,
            indent=self.indent,
            sort_keys=self.sort_keys,
            default=str,
        )

    def _to_dict(self, changelog: Changelog) -> Dict[str, Any]:
        """Convert changelog to dictionary."""
        result: Dict[str, Any] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": changelog.title,
            "description": changelog.description,
            "generated_at": self._get_timestamp(),
            "entries": [],
        }

        if self.include_metadata:
            result["metadata"] = changelog.metadata

        for entry in changelog.entries:
            entry_dict = {
                "version": entry.version,
                "previous_version": entry.previous_version,
                "date": entry.date,
                "is_breaking": entry.is_breaking,
                "summary": entry.summary,
                "changes": {
                    "breaking": [
                        self._format_change(c) for c in entry.breaking_changes
                    ],
                    "deprecations": [
                        self._format_change(c) for c in entry.deprecations
                    ],
                    "non_breaking": [
                        self._format_change(c) for c in entry.non_breaking_changes
                    ],
                    "documentation": [
                        self._format_change(c) for c in entry.documentation_changes
                    ],
                },
            }

            if self.include_metadata:
                entry_dict["metadata"] = entry.metadata

            result["entries"].append(entry_dict)

        return result

    def _format_change(self, classified_change: Any) -> Dict[str, Any]:
        """Format a single change."""
        change = classified_change.change
        return {
            "path": change.path,
            "type": change.change_type.value,
            "description": change.description,
            "impact": classified_change.impact_description,
            "severity": classified_change.severity.value,
            "migration_hint": classified_change.migration_hint,
            "old_value": change.old_value,
            "new_value": change.new_value,
        }

    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"
