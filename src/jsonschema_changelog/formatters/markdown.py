"""Markdown formatter for changelogs."""

from typing import Any, List

from jsonschema_changelog.changelog import Changelog, VersionEntry
from jsonschema_changelog.classifier import ChangeCategory, ClassifiedChange


class MarkdownFormatter:
    """Format changelog as Markdown.

    Generates a CHANGELOG.md compatible format with sections
    for breaking changes, features, and deprecations.

    Example:
        >>> formatter = MarkdownFormatter()
        >>> markdown = formatter.format(changelog)
    """

    def __init__(
        self,
        include_toc: bool = True,
        include_summary: bool = True,
        show_paths: bool = True,
        show_migration_hints: bool = True,
    ) -> None:
        """Initialize MarkdownFormatter.

        Args:
            include_toc: Include table of contents
            include_summary: Include change summary
            show_paths: Show schema paths in changes
            show_migration_hints: Show migration hints for breaking changes
        """
        self.include_toc = include_toc
        self.include_summary = include_summary
        self.show_paths = show_paths
        self.show_migration_hints = show_migration_hints

    def format(self, changelog: Changelog) -> str:
        """Format a changelog as Markdown.

        Args:
            changelog: The changelog to format

        Returns:
            Markdown formatted string
        """
        lines: List[str] = []

        # Title
        lines.append(f"# {changelog.title}")
        lines.append("")

        if changelog.description:
            lines.append(changelog.description)
            lines.append("")

        # Table of contents
        if self.include_toc and len(changelog.entries) > 1:
            lines.extend(self._format_toc(changelog))
            lines.append("")

        # Version entries
        for entry in changelog.entries:
            lines.extend(self._format_entry(entry))
            lines.append("")

        return "\n".join(lines)

    def _format_toc(self, changelog: Changelog) -> List[str]:
        """Format table of contents."""
        lines = [
            "## Table of Contents",
            "",
        ]

        for entry in changelog.entries:
            version = entry.version
            anchor = version.replace(".", "").lower()
            breaking_badge = " 🚨" if entry.is_breaking else ""
            lines.append(f"- [{version}](#{anchor}){breaking_badge}")

        return lines

    def _format_entry(self, entry: VersionEntry) -> List[str]:
        """Format a version entry."""
        lines: List[str] = []

        # Version header with badges
        version_header = f"## [{entry.version}]"
        if entry.is_breaking:
            version_header += " 🚨 BREAKING CHANGES"
        lines.append(version_header)
        lines.append("")

        # Metadata
        lines.append(f"**Date:** {entry.date}")
        lines.append(f"**Previous Version:** {entry.previous_version}")
        lines.append("")

        # Summary
        if self.include_summary:
            lines.extend(self._format_summary(entry))
            lines.append("")

        # Breaking changes (most important first)
        if entry.breaking_changes:
            lines.extend(
                self._format_change_section(
                    "🚨 Breaking Changes", entry.breaking_changes
                )
            )
            lines.append("")

        # Deprecations
        if entry.deprecations:
            lines.extend(
                self._format_change_section(
                    "⚠️ Deprecations", entry.deprecations
                )
            )
            lines.append("")

        # Non-breaking changes
        if entry.non_breaking_changes:
            lines.extend(
                self._format_change_section(
                    "✨ Changes", entry.non_breaking_changes
                )
            )
            lines.append("")

        # Documentation changes
        if entry.documentation_changes:
            lines.extend(
                self._format_change_section(
                    "📝 Documentation", entry.documentation_changes
                )
            )
            lines.append("")

        return lines

    def _format_summary(self, entry: VersionEntry) -> List[str]:
        """Format change summary."""
        lines = ["### Summary", ""]

        summary = entry.summary
        total = summary.get("total", 0)

        lines.append(f"| Category | Count |")
        lines.append("| --- | --- |")

        if summary.get("breaking", 0) > 0:
            lines.append(f"| 🚨 Breaking | {summary['breaking']} |")
        if summary.get("deprecation", 0) > 0:
            lines.append(f"| ⚠️ Deprecations | {summary['deprecation']} |")
        if summary.get("non_breaking", 0) > 0:
            lines.append(f"| ✨ Non-breaking | {summary['non_breaking']} |")
        if summary.get("documentation", 0) > 0:
            lines.append(f"| 📝 Documentation | {summary['documentation']} |")

        lines.append(f"| **Total** | **{total}** |")

        return lines

    def _format_change_section(
        self, title: str, changes: List[ClassifiedChange]
    ) -> List[str]:
        """Format a section of changes."""
        lines = [f"### {title}", ""]

        for change in changes:
            lines.extend(self._format_change(change))

        return lines

    def _format_change(self, classified_change: ClassifiedChange) -> List[str]:
        """Format a single change."""
        lines: List[str] = []
        change = classified_change.change

        # Main description
        description = change.description
        lines.append(f"- **{description}**")

        # Path
        if self.show_paths:
            lines.append(f"  - Path: `{change.path}`")

        # Impact
        lines.append(f"  - Impact: {classified_change.impact_description}")

        # Migration hint for breaking changes
        if (
            self.show_migration_hints
            and classified_change.category == ChangeCategory.BREAKING
            and classified_change.migration_hint
        ):
            lines.append(f"  - 🛠️ Migration: {classified_change.migration_hint}")

        # Values changed
        if change.old_value is not None or change.new_value is not None:
            if change.old_value is not None and change.new_value is not None:
                lines.append(
                    f"  - Changed: `{change.old_value}` → `{change.new_value}`"
                )
            elif change.old_value is not None:
                lines.append(f"  - Removed: `{change.old_value}`")
            else:
                lines.append(f"  - Added: `{change.new_value}`")

        return lines
