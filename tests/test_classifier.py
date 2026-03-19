"""Tests for the classifier module."""

import json
from pathlib import Path

import pytest

from jsonschema_changelog.classifier import (
    ChangeCategory,
    ChangeClassifier,
    ClassificationResult,
    Severity,
    classify_changes,
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
def schema_v3():
    with open(FIXTURES_DIR / "schema_v3_breaking.json") as f:
        return json.load(f)


class TestChangeClassifier:
    """Tests for ChangeClassifier class."""

    def test_property_removed_is_breaking(self):
        """Removing a property should be classified as breaking."""
        change = SchemaChange(
            path="properties.name",
            change_type=ChangeType.REMOVED,
            old_value={"type": "string"},
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.breaking_changes) == 1
        assert result.breaking_changes[0].category == ChangeCategory.BREAKING

    def test_required_added_is_breaking(self):
        """Adding a required field should be breaking."""
        change = SchemaChange(
            path="name",
            change_type=ChangeType.REQUIRED_ADDED,
            new_value=True,
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.breaking_changes) == 1

    def test_enum_removed_is_breaking(self):
        """Removing enum values should be breaking."""
        change = SchemaChange(
            path="properties.status",
            change_type=ChangeType.ENUM_REMOVED,
            old_value=["x"],
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.breaking_changes) == 1

    def test_property_added_is_non_breaking(self):
        """Adding a property should be non-breaking."""
        change = SchemaChange(
            path="properties.email",
            change_type=ChangeType.ADDED,
            new_value={"type": "string"},
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.non_breaking_changes) == 1
        assert result.is_compatible

    def test_required_removed_is_non_breaking(self):
        """Removing required should be non-breaking."""
        change = SchemaChange(
            path="name",
            change_type=ChangeType.REQUIRED_REMOVED,
            old_value=True,
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.non_breaking_changes) == 1

    def test_enum_added_is_non_breaking(self):
        """Adding enum values should be non-breaking."""
        change = SchemaChange(
            path="properties.status",
            change_type=ChangeType.ENUM_ADDED,
            new_value=["new_value"],
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.non_breaking_changes) == 1

    def test_deprecation_detected(self):
        """Deprecation should be detected."""
        change = SchemaChange(
            path="properties.legacy",
            change_type=ChangeType.DEPRECATED,
            new_value=True,
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.deprecations) == 1

    def test_description_change_is_documentation(self):
        """Description changes should be documentation."""
        change = SchemaChange(
            path="properties.name",
            change_type=ChangeType.DESCRIPTION_CHANGED,
            old_value="Old desc",
            new_value="New desc",
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.documentation_changes) == 1

    def test_type_change_integer_to_number_is_non_breaking(self):
        """Widening type from integer to number is non-breaking."""
        change = SchemaChange(
            path="properties.count",
            change_type=ChangeType.TYPE_CHANGED,
            old_value="integer",
            new_value="number",
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.non_breaking_changes) == 1

    def test_type_change_string_to_integer_is_breaking(self):
        """Narrowing type from string to integer is breaking."""
        change = SchemaChange(
            path="properties.value",
            change_type=ChangeType.TYPE_CHANGED,
            old_value="string",
            new_value="integer",
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.breaking_changes) == 1

    def test_minlength_increased_is_breaking(self):
        """Increasing minLength is breaking."""
        change = SchemaChange(
            path="properties.name",
            change_type=ChangeType.CONSTRAINT_CHANGED,
            old_value=5,
            new_value=10,
            metadata={"constraint": "minLength"},
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.breaking_changes) == 1

    def test_maxlength_decreased_is_breaking(self):
        """Decreasing maxLength is breaking."""
        change = SchemaChange(
            path="properties.name",
            change_type=ChangeType.CONSTRAINT_CHANGED,
            old_value=100,
            new_value=50,
            metadata={"constraint": "maxLength"},
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.breaking_changes) == 1

    def test_maxlength_increased_is_non_breaking(self):
        """Increasing maxLength is non-breaking."""
        change = SchemaChange(
            path="properties.name",
            change_type=ChangeType.CONSTRAINT_CHANGED,
            old_value=50,
            new_value=100,
            metadata={"constraint": "maxLength"},
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert len(result.non_breaking_changes) == 1

    def test_fixture_v1_to_v2_is_compatible(self, schema_v1, schema_v2):
        """v1 to v2 should be backward compatible."""
        differ = SchemaDiff()
        diff_result = differ.compare(schema_v1, schema_v2)
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        # v2 only adds optional properties and expands enums
        assert result.is_compatible
        assert len(result.breaking_changes) == 0

    def test_fixture_v2_to_v3_is_not_compatible(self, schema_v2, schema_v3):
        """v2 to v3 should NOT be backward compatible."""
        differ = SchemaDiff()
        diff_result = differ.compare(schema_v2, schema_v3)
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        # v3 has breaking changes
        assert not result.is_compatible
        assert len(result.breaking_changes) > 0

    def test_strict_mode(self):
        """Test strict mode treats ambiguous as breaking."""
        change = SchemaChange(
            path="properties.data",
            change_type=ChangeType.MODIFIED,
            old_value="old",
            new_value="new",
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        # Non-strict mode
        classifier = ChangeClassifier(strict_mode=False)
        result = classifier.classify(diff_result)
        assert len(result.breaking_changes) == 0
        
        # Strict mode
        classifier_strict = ChangeClassifier(strict_mode=True)
        result_strict = classifier_strict.classify(diff_result)
        assert len(result_strict.breaking_changes) == 1

    def test_summary_counts(self):
        """Test summary calculation."""
        changes = [
            SchemaChange(path="a", change_type=ChangeType.REMOVED),
            SchemaChange(path="b", change_type=ChangeType.ADDED),
            SchemaChange(path="c", change_type=ChangeType.ADDED),
            SchemaChange(path="d", change_type=ChangeType.DEPRECATED),
        ]
        diff_result = DiffResult(old_version="1", new_version="2", changes=changes)
        
        classifier = ChangeClassifier()
        result = classifier.classify(diff_result)
        
        assert result.summary["breaking"] == 1
        assert result.summary["non_breaking"] == 2
        assert result.summary["deprecation"] == 1
        assert result.summary["total"] == 4


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_classify_changes_function(self):
        """Test classify_changes convenience function."""
        change = SchemaChange(
            path="properties.name",
            change_type=ChangeType.REMOVED,
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        
        result = classify_changes(diff_result)
        assert isinstance(result, ClassificationResult)
        assert len(result.breaking_changes) == 1
