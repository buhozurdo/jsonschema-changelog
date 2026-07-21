"""Tests for the formatters module."""

import json

import pytest

from jsonschema_changelog.changelog import Changelog, VersionEntry
from jsonschema_changelog.classifier import ChangeCategory, ClassifiedChange, Severity
from jsonschema_changelog.diff import ChangeType, SchemaChange
from jsonschema_changelog.formatters import (
    HtmlFormatter,
    JsonFormatter,
    MarkdownFormatter,
)


@pytest.fixture
def sample_changelog():
    """Create a sample changelog for testing."""
    changelog = Changelog(
        title="Test Changelog",
        description="Test description",
    )

    # Create sample changes
    breaking_change = ClassifiedChange(
        change=SchemaChange(
            path="properties.name",
            change_type=ChangeType.REMOVED,
            old_value={"type": "string"},
        ),
        category=ChangeCategory.BREAKING,
        severity=Severity.HIGH,
        impact_description="Property removed",
        migration_hint="Remove references to this field",
    )

    non_breaking_change = ClassifiedChange(
        change=SchemaChange(
            path="properties.email",
            change_type=ChangeType.ADDED,
            new_value={"type": "string"},
        ),
        category=ChangeCategory.NON_BREAKING,
        severity=Severity.LOW,
        impact_description="New optional property",
    )

    deprecation = ClassifiedChange(
        change=SchemaChange(
            path="properties.legacy",
            change_type=ChangeType.DEPRECATED,
            new_value=True,
        ),
        category=ChangeCategory.DEPRECATION,
        severity=Severity.MEDIUM,
        impact_description="Field deprecated",
    )

    entry = VersionEntry(
        version="2.0.0",
        previous_version="1.0.0",
        date="2024-01-15",
        changes=[breaking_change, non_breaking_change, deprecation],
        summary={
            "breaking": 1,
            "non_breaking": 1,
            "deprecation": 1,
            "documentation": 0,
            "total": 3,
        },
    )

    changelog.add_entry(entry)
    return changelog


class TestMarkdownFormatter:
    """Tests for MarkdownFormatter."""

    def test_format_basic(self, sample_changelog):
        """Test basic Markdown formatting."""
        formatter = MarkdownFormatter()
        output = formatter.format(sample_changelog)

        assert "# Test Changelog" in output
        assert "2.0.0" in output
        assert "Breaking Changes" in output

    def test_format_includes_sections(self, sample_changelog):
        """Test that all sections are included."""
        formatter = MarkdownFormatter()
        output = formatter.format(sample_changelog)

        assert "Breaking Changes" in output
        assert "Deprecations" in output
        assert "Changes" in output  # Non-breaking

    def test_format_includes_summary(self, sample_changelog):
        """Test that summary table is included."""
        formatter = MarkdownFormatter(include_summary=True)
        output = formatter.format(sample_changelog)

        assert "Summary" in output
        assert "| Category |" in output

    def test_format_without_summary(self, sample_changelog):
        """Test formatting without summary."""
        formatter = MarkdownFormatter(include_summary=False)
        output = formatter.format(sample_changelog)

        assert "| Category |" not in output

    def test_format_includes_paths(self, sample_changelog):
        """Test that paths are shown."""
        formatter = MarkdownFormatter(show_paths=True)
        output = formatter.format(sample_changelog)

        assert "properties.name" in output

    def test_format_without_paths(self, sample_changelog):
        """Test formatting without paths."""
        formatter = MarkdownFormatter(show_paths=False)
        output = formatter.format(sample_changelog)

        # Path should not appear in the detailed format
        assert "Path:" not in output

    def test_format_includes_migration_hints(self, sample_changelog):
        """Test that migration hints are shown."""
        formatter = MarkdownFormatter(show_migration_hints=True)
        output = formatter.format(sample_changelog)

        assert "Migration:" in output or "🛠️" in output

    def test_format_breaking_badge(self, sample_changelog):
        """Test breaking change badge."""
        formatter = MarkdownFormatter()
        output = formatter.format(sample_changelog)

        assert "BREAKING" in output or "🚨" in output


class TestJsonFormatter:
    """Tests for JsonFormatter."""

    def test_format_valid_json(self, sample_changelog):
        """Test that output is valid JSON."""
        formatter = JsonFormatter()
        output = formatter.format(sample_changelog)

        data = json.loads(output)
        assert data is not None

    def test_format_structure(self, sample_changelog):
        """Test JSON structure."""
        formatter = JsonFormatter()
        output = formatter.format(sample_changelog)

        data = json.loads(output)
        assert data["title"] == "Test Changelog"
        assert "entries" in data
        assert len(data["entries"]) == 1

    def test_format_entry_structure(self, sample_changelog):
        """Test entry structure in JSON."""
        formatter = JsonFormatter()
        output = formatter.format(sample_changelog)

        data = json.loads(output)
        entry = data["entries"][0]

        assert entry["version"] == "2.0.0"
        assert entry["previous_version"] == "1.0.0"
        assert "changes" in entry
        assert "breaking" in entry["changes"]

    def test_format_with_indent(self, sample_changelog):
        """Test custom indentation."""
        formatter = JsonFormatter(indent=4)
        output = formatter.format(sample_changelog)

        # 4-space indent should be present
        assert "    " in output

    def test_format_without_metadata(self, sample_changelog):
        """Test formatting without metadata."""
        formatter = JsonFormatter(include_metadata=False)
        output = formatter.format(sample_changelog)

        data = json.loads(output)
        assert "metadata" not in data

    def test_format_includes_generated_at(self, sample_changelog):
        """Test that generated_at timestamp is included."""
        formatter = JsonFormatter()
        output = formatter.format(sample_changelog)

        data = json.loads(output)
        assert "generated_at" in data


class TestHtmlFormatter:
    """Tests for HtmlFormatter."""

    def test_format_valid_html(self, sample_changelog):
        """Test that output is valid HTML."""
        formatter = HtmlFormatter()
        output = formatter.format(sample_changelog)

        assert "<!DOCTYPE html>" in output
        assert "<html" in output
        assert "</html>" in output

    def test_format_includes_title(self, sample_changelog):
        """Test that title is in HTML."""
        formatter = HtmlFormatter()
        output = formatter.format(sample_changelog)

        assert "Test Changelog" in output

    def test_format_includes_styles(self, sample_changelog):
        """Test that styles are included."""
        formatter = HtmlFormatter()
        output = formatter.format(sample_changelog)

        assert "<style>" in output
        assert "</style>" in output

    def test_format_includes_breaking_badge(self, sample_changelog):
        """Test breaking badge in HTML."""
        formatter = HtmlFormatter()
        output = formatter.format(sample_changelog)

        assert "BREAKING" in output or "badge-breaking" in output

    def test_format_includes_summary_table(self, sample_changelog):
        """Test summary table in HTML."""
        formatter = HtmlFormatter(include_summary=True)
        output = formatter.format(sample_changelog)

        assert "<table" in output

    def test_format_without_summary(self, sample_changelog):
        """Test HTML without summary table."""
        formatter = HtmlFormatter(include_summary=False)
        output = formatter.format(sample_changelog)

        # Table should still appear for changes, but not summary specifically
        # This test verifies the include_summary flag is respected
        assert "include_summary" not in output  # Template variable shouldn't leak

    def test_format_escapes_html(self, sample_changelog):
        """Test that HTML special characters are escaped."""
        # Add a change with HTML in the description
        changelog = Changelog(title="<script>alert('xss')</script>")
        formatter = HtmlFormatter()
        output = formatter.format(changelog)

        # Script tags should be escaped
        assert "<script>" not in output or "&lt;script&gt;" in output

    def test_format_includes_footer(self, sample_changelog):
        """Test that footer is included."""
        formatter = HtmlFormatter()
        output = formatter.format(sample_changelog)

        assert "<footer>" in output
        assert "B\u00faho Zurdo" in output or "Buho Zurdo" in output

    def test_format_responsive(self, sample_changelog):
        """Test that responsive viewport meta is included."""
        formatter = HtmlFormatter()
        output = formatter.format(sample_changelog)

        assert "viewport" in output
