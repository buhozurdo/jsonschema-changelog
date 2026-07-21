"""Tests for the changelog module."""

import json
from pathlib import Path

import pytest

from jsonschema_changelog.changelog import Changelog, ChangelogGenerator, VersionEntry
from jsonschema_changelog.classifier import (
    ChangeCategory,
    ChangeClassifier,
    ClassifiedChange,
    Severity,
)
from jsonschema_changelog.diff import ChangeType, DiffResult, SchemaChange, SchemaDiff

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def schema_v1():
    with open(FIXTURES_DIR / "schema_v1.json") as f:
        return json.load(f)


@pytest.fixture
def schema_v2():
    with open(FIXTURES_DIR / "schema_v2.json") as f:
        return json.load(f)


@pytest.fixture
def sample_classification():
    """Create a sample classification result."""
    changes = [
        SchemaChange(path="properties.name", change_type=ChangeType.REMOVED),
        SchemaChange(
            path="properties.email",
            change_type=ChangeType.ADDED,
            new_value={"type": "string"},
        ),
        SchemaChange(path="properties.legacy", change_type=ChangeType.DEPRECATED),
    ]
    diff_result = DiffResult(old_version="1.0.0", new_version="2.0.0", changes=changes)
    classifier = ChangeClassifier()
    return classifier.classify(diff_result)


class TestChangelogGenerator:
    """Tests for ChangelogGenerator class."""

    def test_generate_changelog(self, sample_classification):
        """Test basic changelog generation."""
        generator = ChangelogGenerator(title="Test Changelog")
        changelog = generator.generate(sample_classification)

        assert changelog.title == "Test Changelog"
        assert len(changelog.entries) == 1
        assert changelog.entries[0].version == "2.0.0"

    def test_changelog_entry_properties(self, sample_classification):
        """Test changelog entry has correct properties."""
        generator = ChangelogGenerator()
        changelog = generator.generate(sample_classification, date="2024-01-15")

        entry = changelog.entries[0]
        assert entry.version == "2.0.0"
        assert entry.previous_version == "1.0.0"
        assert entry.date == "2024-01-15"
        assert entry.is_breaking  # Has a removed property

    def test_format_markdown(self, sample_classification):
        """Test Markdown formatting."""
        generator = ChangelogGenerator(title="Test")
        changelog = generator.generate(sample_classification)
        md = generator.to_markdown(changelog)

        assert "# Test" in md
        assert "Breaking Changes" in md
        assert "2.0.0" in md

    def test_format_json(self, sample_classification):
        """Test JSON formatting."""
        generator = ChangelogGenerator(title="Test")
        changelog = generator.generate(sample_classification)
        json_str = generator.to_json(changelog)

        data = json.loads(json_str)
        assert data["title"] == "Test"
        assert len(data["entries"]) == 1

    def test_format_html(self, sample_classification):
        """Test HTML formatting."""
        generator = ChangelogGenerator(title="Test")
        changelog = generator.generate(sample_classification)
        html = generator.to_html(changelog)

        assert "<html" in html
        assert "Test" in html
        assert "Breaking" in html

    def test_multi_version_changelog(self):
        """Test multi-version changelog generation."""
        # Create multiple classification results
        changes1 = [SchemaChange(path="a", change_type=ChangeType.ADDED)]
        diff1 = DiffResult(old_version="1.0.0", new_version="1.1.0", changes=changes1)

        changes2 = [SchemaChange(path="b", change_type=ChangeType.REMOVED)]
        diff2 = DiffResult(old_version="1.1.0", new_version="2.0.0", changes=changes2)

        classifier = ChangeClassifier()
        results = [classifier.classify(diff1), classifier.classify(diff2)]

        generator = ChangelogGenerator()
        changelog = generator.generate_multi(
            results, dates=["2024-01-01", "2024-02-01"]
        )

        assert len(changelog.entries) == 2
        assert changelog.entries[0].version == "1.1.0"
        assert changelog.entries[1].version == "2.0.0"

    def test_fixture_schemas_changelog(self, schema_v1, schema_v2):
        """Test changelog generation with fixture schemas."""
        differ = SchemaDiff(old_version="1.0.0", new_version="2.0.0")
        diff_result = differ.compare(schema_v1, schema_v2)

        classifier = ChangeClassifier()
        classification = classifier.classify(diff_result)

        generator = ChangelogGenerator(title="Laboratory Sample Schema Changelog")
        changelog = generator.generate(classification)

        assert changelog.title == "Laboratory Sample Schema Changelog"
        entry = changelog.entries[0]

        # v1 to v2 should NOT be breaking
        assert not entry.is_breaking
        assert len(entry.non_breaking_changes) > 0

    def test_include_documentation_option(self, sample_classification):
        """Test include_documentation option."""
        # Add a documentation change
        sample_classification.changes[:]
        doc_change = ClassifiedChange(
            change=SchemaChange(
                path="root", change_type=ChangeType.DESCRIPTION_CHANGED
            ),
            category=ChangeCategory.DOCUMENTATION,
            severity=Severity.INFO,
            impact_description="Description updated",
        )
        sample_classification.changes.append(doc_change)

        # Without documentation
        generator_no_docs = ChangelogGenerator(include_documentation=False)
        changelog_no_docs = generator_no_docs.generate(sample_classification)
        entry = changelog_no_docs.entries[0]

        # Documentation changes should be filtered
        assert len(entry.documentation_changes) == 0


class TestChangelog:
    """Tests for Changelog dataclass."""

    def test_get_entry(self):
        """Test getting entry by version."""
        changelog = Changelog(title="Test")
        entry = VersionEntry(
            version="1.0.0", previous_version="0.9.0", date="2024-01-01"
        )
        changelog.add_entry(entry)

        found = changelog.get_entry("1.0.0")
        assert found is not None
        assert found.version == "1.0.0"

        not_found = changelog.get_entry("2.0.0")
        assert not_found is None

    def test_latest_entry(self):
        """Test latest entry property."""
        changelog = Changelog(title="Test")
        assert changelog.latest_entry is None

        entry = VersionEntry(
            version="1.0.0", previous_version="0.9.0", date="2024-01-01"
        )
        changelog.add_entry(entry)

        assert changelog.latest_entry == entry

    def test_has_breaking_changes(self):
        """Test has_breaking_changes property."""
        changelog = Changelog(title="Test")
        entry = VersionEntry(
            version="1.0.0",
            previous_version="0.9.0",
            date="2024-01-01",
            summary={"breaking": 1},
        )
        # Need to add a breaking change
        entry.changes.append(
            ClassifiedChange(
                change=SchemaChange(path="x", change_type=ChangeType.REMOVED),
                category=ChangeCategory.BREAKING,
                severity=Severity.HIGH,
                impact_description="Breaking",
            )
        )
        changelog.add_entry(entry)

        assert changelog.has_breaking_changes

    def test_to_dict(self):
        """Test serialization."""
        changelog = Changelog(title="Test", description="Description")
        entry = VersionEntry(
            version="1.0.0", previous_version="0.9.0", date="2024-01-01"
        )
        changelog.add_entry(entry)

        data = changelog.to_dict()
        assert data["title"] == "Test"
        assert data["description"] == "Description"
        assert len(data["entries"]) == 1
