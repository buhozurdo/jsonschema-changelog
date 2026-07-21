"""Changelog generation module.

This module provides the ChangelogGenerator class for generating
changelogs from classified schema changes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Type

from jsonschema_changelog.classifier import (
    ChangeCategory,
    ClassificationResult,
    ClassifiedChange,
)


class Formatter(Protocol):
    """Protocol for changelog formatters."""

    def format(self, changelog: "Changelog") -> str:
        """Format a changelog to string."""
        ...


@dataclass
class VersionEntry:
    """A single version entry in the changelog."""

    version: str
    previous_version: str
    date: str
    changes: List[ClassifiedChange] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def breaking_changes(self) -> List[ClassifiedChange]:
        """Get breaking changes for this version."""
        return [c for c in self.changes if c.category == ChangeCategory.BREAKING]

    @property
    def non_breaking_changes(self) -> List[ClassifiedChange]:
        """Get non-breaking changes for this version."""
        return [c for c in self.changes if c.category == ChangeCategory.NON_BREAKING]

    @property
    def deprecations(self) -> List[ClassifiedChange]:
        """Get deprecations for this version."""
        return [c for c in self.changes if c.category == ChangeCategory.DEPRECATION]

    @property
    def documentation_changes(self) -> List[ClassifiedChange]:
        """Get documentation changes for this version."""
        return [c for c in self.changes if c.category == ChangeCategory.DOCUMENTATION]

    @property
    def is_breaking(self) -> bool:
        """Check if this version has breaking changes."""
        return len(self.breaking_changes) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "version": self.version,
            "previous_version": self.previous_version,
            "date": self.date,
            "is_breaking": self.is_breaking,
            "summary": self.summary,
            "changes": [c.to_dict() for c in self.changes],
            "metadata": self.metadata,
        }


@dataclass
class Changelog:
    """Complete changelog with multiple version entries."""

    title: str
    description: str = ""
    entries: List[VersionEntry] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_entry(self, entry: VersionEntry) -> None:
        """Add a version entry to the changelog."""
        self.entries.append(entry)

    def get_entry(self, version: str) -> Optional[VersionEntry]:
        """Get a specific version entry."""
        for entry in self.entries:
            if entry.version == version:
                return entry
        return None

    @property
    def latest_entry(self) -> Optional[VersionEntry]:
        """Get the most recent entry."""
        return self.entries[0] if self.entries else None

    @property
    def has_breaking_changes(self) -> bool:
        """Check if any version has breaking changes."""
        return any(e.is_breaking for e in self.entries)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "description": self.description,
            "entries": [e.to_dict() for e in self.entries],
            "metadata": self.metadata,
        }


class ChangelogGenerator:
    """Generate changelogs from classified schema changes.

    This class takes classification results and generates structured
    changelogs that can be formatted in different ways.

    Example:
        >>> generator = ChangelogGenerator(title="API Schema Changelog")
        >>> changelog = generator.generate(classification_result)
        >>> markdown = generator.to_markdown(changelog)

    """

    def __init__(
        self,
        title: str = "Schema Changelog",
        description: str = "",
        include_documentation: bool = False,
    ) -> None:
        """Initialize ChangelogGenerator.

        Args:
            title: Title for the changelog
            description: Description of the changelog
            include_documentation: Whether to include documentation changes

        """
        self.title = title
        self.description = description
        self.include_documentation = include_documentation
        self._formatters: Dict[str, Type[Formatter]] = {}

    def register_formatter(self, name: str, formatter_class: Type[Formatter]) -> None:
        """Register a custom formatter."""
        self._formatters[name] = formatter_class

    def generate(
        self,
        classification_result: ClassificationResult,
        date: Optional[str] = None,
    ) -> Changelog:
        """Generate a changelog from a classification result.

        Args:
            classification_result: The classified changes
            date: Optional date string (defaults to today)

        Returns:
            Changelog with the changes

        """
        changelog = Changelog(
            title=self.title,
            description=self.description,
            metadata=classification_result.metadata.copy(),
        )

        entry = self._create_entry(classification_result, date)
        changelog.add_entry(entry)

        return changelog

    def generate_multi(
        self,
        classification_results: List[ClassificationResult],
        dates: Optional[List[str]] = None,
    ) -> Changelog:
        """Generate a changelog from multiple classification results.

        Args:
            classification_results: List of classified changes
            dates: Optional list of date strings

        Returns:
            Changelog with all version entries

        """
        changelog = Changelog(
            title=self.title,
            description=self.description,
        )

        for i, result in enumerate(classification_results):
            date = dates[i] if dates and i < len(dates) else None
            entry = self._create_entry(result, date)
            changelog.add_entry(entry)

        return changelog

    def _create_entry(
        self,
        classification_result: ClassificationResult,
        date: Optional[str] = None,
    ) -> VersionEntry:
        """Create a version entry from a classification result."""
        changes = classification_result.changes

        # Filter out documentation changes if not included
        if not self.include_documentation:
            changes = [c for c in changes if c.category != ChangeCategory.DOCUMENTATION]

        # Calculate summary
        summary = {
            "breaking": sum(
                1 for c in changes if c.category == ChangeCategory.BREAKING
            ),
            "non_breaking": sum(
                1 for c in changes if c.category == ChangeCategory.NON_BREAKING
            ),
            "deprecation": sum(
                1 for c in changes if c.category == ChangeCategory.DEPRECATION
            ),
            "documentation": sum(
                1 for c in changes if c.category == ChangeCategory.DOCUMENTATION
            ),
            "total": len(changes),
        }

        return VersionEntry(
            version=classification_result.new_version,
            previous_version=classification_result.old_version,
            date=date or datetime.now().strftime("%Y-%m-%d"),
            changes=changes,
            summary=summary,
            metadata=classification_result.metadata.copy(),
        )

    def format(
        self,
        changelog: Changelog,
        format_type: str = "markdown",
        **kwargs: Any,
    ) -> str:
        """Format a changelog using the specified formatter.

        Args:
            changelog: The changelog to format
            format_type: The format type (markdown, json, html)
            **kwargs: Additional arguments for the formatter

        Returns:
            Formatted changelog string

        """
        # Import formatters lazily to avoid circular imports
        if format_type == "markdown":
            from jsonschema_changelog.formatters.markdown import MarkdownFormatter

            formatter = MarkdownFormatter(**kwargs)
        elif format_type == "json":
            from jsonschema_changelog.formatters.json import JsonFormatter

            formatter = JsonFormatter(**kwargs)
        elif format_type == "html":
            from jsonschema_changelog.formatters.html import HtmlFormatter

            formatter = HtmlFormatter(**kwargs)
        elif format_type in self._formatters:
            formatter = self._formatters[format_type](**kwargs)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

        return formatter.format(changelog)

    def to_markdown(self, changelog: Changelog, **kwargs: Any) -> str:
        """Convenience method to format as Markdown."""
        return self.format(changelog, "markdown", **kwargs)

    def to_json(self, changelog: Changelog, **kwargs: Any) -> str:
        """Convenience method to format as JSON."""
        return self.format(changelog, "json", **kwargs)

    def to_html(self, changelog: Changelog, **kwargs: Any) -> str:
        """Convenience method to format as HTML."""
        return self.format(changelog, "html", **kwargs)
