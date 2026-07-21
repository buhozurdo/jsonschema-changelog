"""Tests for the compatibility module."""

import json
from pathlib import Path

import pytest

from jsonschema_changelog.compatibility import (
    CompatibilityLevel,
    CompatibilityResult,
    CompatibilityValidator,
    validate_compatibility,
)

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


class TestCompatibilityValidator:
    """Tests for CompatibilityValidator class."""

    def test_identical_schemas_fully_compatible(self):
        """Identical schemas should be fully compatible."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        validator = CompatibilityValidator()
        result = validator.validate(schema, schema)

        assert result.level == CompatibilityLevel.FULL
        assert result.is_backward_compatible
        assert result.is_forward_compatible
        assert result.is_fully_compatible

    def test_adding_optional_property_backward_compatible(self):
        """Adding an optional property should be backward compatible."""
        old = {"type": "object", "properties": {"a": {"type": "string"}}}
        new = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
            },
        }

        validator = CompatibilityValidator()
        result = validator.validate(old, new)

        assert result.is_backward_compatible

    def test_removing_property_not_backward_compatible(self):
        """Removing a property should NOT be backward compatible."""
        old = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
            },
        }
        new = {"type": "object", "properties": {"a": {"type": "string"}}}

        validator = CompatibilityValidator()
        result = validator.validate(old, new)

        assert not result.is_backward_compatible
        assert len(result.issues) > 0

    def test_adding_required_not_backward_compatible(self):
        """Adding a required field should NOT be backward compatible."""
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

        validator = CompatibilityValidator()
        result = validator.validate(old, new)

        assert not result.is_backward_compatible

    def test_removing_required_backward_compatible(self):
        """Removing required should be backward compatible."""
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

        validator = CompatibilityValidator()
        result = validator.validate(old, new)

        assert result.is_backward_compatible

    def test_fixture_v1_to_v2_backward_compatible(self, schema_v1, schema_v2):
        """v1 to v2 should be backward compatible."""
        validator = CompatibilityValidator()
        result = validator.validate(schema_v1, schema_v2, "1.0.0", "2.0.0")

        assert result.is_backward_compatible
        assert result.old_version == "1.0.0"
        assert result.new_version == "2.0.0"

    def test_fixture_v2_to_v3_not_backward_compatible(self, schema_v2, schema_v3):
        """v2 to v3 should NOT be backward compatible."""
        validator = CompatibilityValidator()
        result = validator.validate(schema_v2, schema_v3)

        assert not result.is_backward_compatible
        assert result.level in (CompatibilityLevel.FORWARD, CompatibilityLevel.NONE)
        assert len(result.issues) > 0

    def test_quick_backward_check(self, schema_v1, schema_v2):
        """Test quick backward compatibility check."""
        validator = CompatibilityValidator()

        assert validator.check_backward_compatibility(schema_v1, schema_v2)

    def test_quick_forward_check(self, schema_v1, schema_v2):
        """Test quick forward compatibility check."""
        validator = CompatibilityValidator()

        # v1 to v2 is NOT forward compatible (v2 has new enum values)
        assert not validator.check_forward_compatibility(schema_v1, schema_v2)

    def test_suggestions_generated(self, schema_v2, schema_v3):
        """Test that suggestions are generated for breaking changes."""
        validator = CompatibilityValidator()
        result = validator.validate(schema_v2, schema_v3)

        # Should have suggestions for fixing issues
        assert len(result.suggestions) > 0

    def test_strict_mode(self):
        """Test strict mode validation."""
        old = {"type": "object", "properties": {"a": {"type": "string"}}}
        new = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
            },
        }

        # Strict mode should flag added properties as forward-incompatible
        validator = CompatibilityValidator(strict_mode=True)
        result = validator.validate(old, new)

        # In strict mode, forward issues should be flagged
        forward_issues = result.get_issues_by_direction("forward")
        assert len(forward_issues) > 0

    def test_to_dict(self):
        """Test result serialization."""
        schema = {"type": "object", "properties": {"a": {"type": "string"}}}

        validator = CompatibilityValidator()
        result = validator.validate(schema, schema, "1.0", "1.0")

        data = result.to_dict()
        assert data["level"] == "full"
        assert data["is_backward_compatible"] is True
        assert data["is_forward_compatible"] is True


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_validate_compatibility_function(self):
        """Test validate_compatibility convenience function."""
        schema = {"type": "object", "properties": {"a": {"type": "string"}}}

        result = validate_compatibility(schema, schema)
        assert isinstance(result, CompatibilityResult)
        assert result.is_fully_compatible
