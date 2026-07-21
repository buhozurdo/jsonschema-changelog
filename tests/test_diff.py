"""Tests for the diff module."""

import json
from pathlib import Path

import pytest

from jsonschema_changelog.diff import ChangeType, SchemaChange, SchemaDiff

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def schema_v1():
    """Load v1 schema fixture."""
    with open(FIXTURES_DIR / "schema_v1.json") as f:
        return json.load(f)


@pytest.fixture
def schema_v2():
    """Load v2 schema fixture."""
    with open(FIXTURES_DIR / "schema_v2.json") as f:
        return json.load(f)


@pytest.fixture
def schema_v3():
    """Load v3 breaking schema fixture."""
    with open(FIXTURES_DIR / "schema_v3_breaking.json") as f:
        return json.load(f)


class TestSchemaDiff:
    """Tests for SchemaDiff class."""

    def test_no_changes_same_schema(self):
        """Test that comparing identical schemas shows no changes."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        differ = SchemaDiff()
        result = differ.compare(schema, schema)

        assert not result.has_changes
        assert result.change_count == 0

    def test_property_added(self):
        """Test detection of added property."""
        old = {"type": "object", "properties": {"a": {"type": "string"}}}
        new = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "integer"},
            },
        }

        differ = SchemaDiff()
        result = differ.compare(old, new)

        assert result.has_changes
        added = result.get_changes_by_type(ChangeType.ADDED)
        assert len(added) == 1
        assert "b" in added[0].path

    def test_property_removed(self):
        """Test detection of removed property."""
        old = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "integer"},
            },
        }
        new = {"type": "object", "properties": {"a": {"type": "string"}}}

        differ = SchemaDiff()
        result = differ.compare(old, new)

        assert result.has_changes
        removed = result.get_changes_by_type(ChangeType.REMOVED)
        assert len(removed) == 1
        assert "b" in removed[0].path

    def test_required_added(self):
        """Test detection of newly required field."""
        old = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "required": [],
        }
        new = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "required": ["a"],
        }

        differ = SchemaDiff()
        result = differ.compare(old, new)

        assert result.has_changes
        req_added = result.get_changes_by_type(ChangeType.REQUIRED_ADDED)
        assert len(req_added) == 1

    def test_required_removed(self):
        """Test detection of field no longer required."""
        old = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "required": ["a"],
        }
        new = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "required": [],
        }

        differ = SchemaDiff()
        result = differ.compare(old, new)

        assert result.has_changes
        req_removed = result.get_changes_by_type(ChangeType.REQUIRED_REMOVED)
        assert len(req_removed) == 1

    def test_type_changed(self):
        """Test detection of type change."""
        old = {"type": "object", "properties": {"a": {"type": "string"}}}
        new = {"type": "object", "properties": {"a": {"type": "integer"}}}

        differ = SchemaDiff()
        result = differ.compare(old, new)

        assert result.has_changes
        type_changes = result.get_changes_by_type(ChangeType.TYPE_CHANGED)
        assert len(type_changes) == 1
        assert type_changes[0].old_value == "string"
        assert type_changes[0].new_value == "integer"

    def test_enum_added(self):
        """Test detection of added enum values."""
        old = {
            "type": "object",
            "properties": {"a": {"type": "string", "enum": ["x", "y"]}},
        }
        new = {
            "type": "object",
            "properties": {"a": {"type": "string", "enum": ["x", "y", "z"]}},
        }

        differ = SchemaDiff()
        result = differ.compare(old, new)

        assert result.has_changes
        enum_added = result.get_changes_by_type(ChangeType.ENUM_ADDED)
        assert len(enum_added) == 1

    def test_enum_removed(self):
        """Test detection of removed enum values."""
        old = {
            "type": "object",
            "properties": {"a": {"type": "string", "enum": ["x", "y", "z"]}},
        }
        new = {
            "type": "object",
            "properties": {"a": {"type": "string", "enum": ["x", "y"]}},
        }

        differ = SchemaDiff()
        result = differ.compare(old, new)

        assert result.has_changes
        enum_removed = result.get_changes_by_type(ChangeType.ENUM_REMOVED)
        assert len(enum_removed) == 1

    def test_constraint_changed(self):
        """Test detection of constraint changes."""
        old = {
            "type": "object",
            "properties": {"a": {"type": "string", "minLength": 5}},
        }
        new = {
            "type": "object",
            "properties": {"a": {"type": "string", "minLength": 10}},
        }

        differ = SchemaDiff()
        result = differ.compare(old, new)

        assert result.has_changes
        constraint_changes = result.get_changes_by_type(ChangeType.CONSTRAINT_CHANGED)
        assert len(constraint_changes) == 1

    def test_format_changed(self):
        """Test detection of format changes."""
        old = {
            "type": "object",
            "properties": {"a": {"type": "string", "format": "email"}},
        }
        new = {
            "type": "object",
            "properties": {"a": {"type": "string", "format": "uri"}},
        }

        differ = SchemaDiff()
        result = differ.compare(old, new)

        assert result.has_changes
        format_changes = result.get_changes_by_type(ChangeType.FORMAT_CHANGED)
        assert len(format_changes) == 1

    def test_fixture_v1_to_v2(self, schema_v1, schema_v2):
        """Test diff between v1 and v2 fixtures."""
        differ = SchemaDiff(old_version="1.0.0", new_version="2.0.0")
        result = differ.compare(schema_v1, schema_v2)

        assert result.has_changes
        assert result.old_version == "1.0.0"
        assert result.new_version == "2.0.0"

        # Should detect: new properties (collector_id, priority, barcode)
        added = result.get_changes_by_type(ChangeType.ADDED)
        assert len(added) == 3

        # Should detect: enum additions (sample_type, status)
        enum_added = result.get_changes_by_type(ChangeType.ENUM_ADDED)
        assert len(enum_added) == 2

        # Should detect: constraint change (notes maxLength)
        constraint_changes = result.get_changes_by_type(ChangeType.CONSTRAINT_CHANGED)
        assert len(constraint_changes) == 1

    def test_fixture_v2_to_v3_breaking(self, schema_v2, schema_v3):
        """Test diff between v2 and v3 (breaking changes)."""
        differ = SchemaDiff(old_version="2.0.0", new_version="3.0.0")
        result = differ.compare(schema_v2, schema_v3)

        assert result.has_changes
        # Should have many breaking changes
        assert result.change_count > 5

    def test_to_dict(self):
        """Test serialization to dictionary."""
        old = {"type": "object", "properties": {"a": {"type": "string"}}}
        new = {"type": "object", "properties": {"a": {"type": "integer"}}}

        differ = SchemaDiff(old_version="1.0", new_version="2.0")
        result = differ.compare(old, new)

        data = result.to_dict()
        assert data["old_version"] == "1.0"
        assert data["new_version"] == "2.0"
        assert "changes" in data
        assert len(data["changes"]) > 0


class TestSchemaChange:
    """Tests for SchemaChange dataclass."""

    def test_auto_description(self):
        """Test automatic description generation."""
        change = SchemaChange(
            path="properties.name",
            change_type=ChangeType.REMOVED,
        )
        assert "properties.name" in change.description
        assert "Removed" in change.description

    def test_custom_description(self):
        """Test custom description."""
        change = SchemaChange(
            path="properties.name",
            change_type=ChangeType.REMOVED,
            description="Custom description",
        )
        assert change.description == "Custom description"

    def test_to_dict(self):
        """Test serialization."""
        change = SchemaChange(
            path="test",
            change_type=ChangeType.ADDED,
            new_value={"type": "string"},
        )
        data = change.to_dict()
        assert data["path"] == "test"
        assert data["change_type"] == "added"
