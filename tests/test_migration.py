"""Tests for the migration module."""

import json
from pathlib import Path

import pytest

from jsonschema_changelog.classifier import ChangeClassifier
from jsonschema_changelog.diff import ChangeType, DiffResult, SchemaChange, SchemaDiff
from jsonschema_changelog.migration import MigrationPlan, MigrationStep, MigrationStrategy, MigrationType

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
def data_samples():
    with open(FIXTURES_DIR / "data_samples.json") as f:
        return json.load(f)


class TestMigrationStrategy:
    """Tests for MigrationStrategy class."""

    def test_generate_plan_for_added_field(self):
        """Test plan generation for added field."""
        change = SchemaChange(
            path="properties.email",
            change_type=ChangeType.ADDED,
            new_value={"type": "string", "default": ""},
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        classifier = ChangeClassifier()
        classification = classifier.classify(diff_result)
        
        strategy = MigrationStrategy()
        plan = strategy.generate(classification)
        
        assert plan.step_count == 1
        assert plan.steps[0].operation == MigrationType.ADD_FIELD

    def test_generate_plan_for_removed_field(self):
        """Test plan generation for removed field."""
        change = SchemaChange(
            path="properties.legacy",
            change_type=ChangeType.REMOVED,
            old_value={"type": "string"},
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        classifier = ChangeClassifier()
        classification = classifier.classify(diff_result)
        
        strategy = MigrationStrategy()
        plan = strategy.generate(classification)
        
        assert plan.step_count == 1
        assert plan.steps[0].operation == MigrationType.REMOVE_FIELD
        assert not plan.steps[0].reversible  # Data loss

    def test_generate_plan_for_type_change(self):
        """Test plan generation for type change."""
        change = SchemaChange(
            path="properties.count",
            change_type=ChangeType.TYPE_CHANGED,
            old_value="string",
            new_value="integer",
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        classifier = ChangeClassifier()
        classification = classifier.classify(diff_result)
        
        strategy = MigrationStrategy()
        plan = strategy.generate(classification)
        
        assert plan.step_count == 1
        assert plan.steps[0].operation == MigrationType.CHANGE_TYPE

    def test_generate_plan_for_required_added(self):
        """Test plan generation for newly required field."""
        change = SchemaChange(
            path="email",
            change_type=ChangeType.REQUIRED_ADDED,
            new_value=True,
            metadata={"field_name": "email"},
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        classifier = ChangeClassifier()
        classification = classifier.classify(diff_result)
        
        strategy = MigrationStrategy()
        plan = strategy.generate(classification)
        
        assert plan.step_count == 1
        assert plan.steps[0].operation == MigrationType.SET_DEFAULT

    def test_execute_migration_add_field(self):
        """Test executing migration to add a field."""
        plan = MigrationPlan(source_version="1", target_version="2")
        plan.add_step(
            MigrationStep(
                operation=MigrationType.ADD_FIELD,
                path="properties.new_field",
                description="Add new_field",
                params={"default_value": "default"},
            )
        )
        
        data = {"existing": "value"}
        
        strategy = MigrationStrategy()
        result = strategy.execute(plan, data)
        
        assert "new_field" in result
        assert result["new_field"] == "default"
        assert result["existing"] == "value"

    def test_execute_migration_remove_field(self):
        """Test executing migration to remove a field."""
        plan = MigrationPlan(source_version="1", target_version="2")
        plan.add_step(
            MigrationStep(
                operation=MigrationType.REMOVE_FIELD,
                path="properties.old_field",
                description="Remove old_field",
            )
        )
        
        data = {"old_field": "value", "keep": "this"}
        
        strategy = MigrationStrategy()
        result = strategy.execute(plan, data)
        
        assert "old_field" not in result
        assert result["keep"] == "this"

    def test_execute_migration_change_type(self):
        """Test executing migration to change type."""
        plan = MigrationPlan(source_version="1", target_version="2")
        plan.add_step(
            MigrationStep(
                operation=MigrationType.CHANGE_TYPE,
                path="properties.count",
                description="Convert count to integer",
                params={"new_type": "integer"},
            )
        )
        
        data = {"count": "42"}
        
        strategy = MigrationStrategy()
        result = strategy.execute(plan, data)
        
        assert result["count"] == 42
        assert isinstance(result["count"], int)

    def test_fixture_v1_to_v2_migration(self, schema_v1, schema_v2, data_samples):
        """Test migration from v1 to v2 schema."""
        differ = SchemaDiff(old_version="1.0.0", new_version="2.0.0")
        diff_result = differ.compare(schema_v1, schema_v2)
        
        classifier = ChangeClassifier()
        classification = classifier.classify(diff_result)
        
        strategy = MigrationStrategy()
        plan = strategy.generate(classification)
        
        # Should have steps for new properties
        assert plan.step_count > 0
        
        # Migrate sample data
        sample = data_samples["valid_v1_sample"]
        migrated = strategy.execute(plan, sample)
        
        # Original data should be preserved
        assert migrated["sample_id"] == sample["sample_id"]
        assert migrated["patient_id"] == sample["patient_id"]

    def test_python_script_generation(self):
        """Test Python migration script generation."""
        plan = MigrationPlan(source_version="1.0", target_version="2.0")
        plan.add_step(
            MigrationStep(
                operation=MigrationType.ADD_FIELD,
                path="properties.email",
                description="Add email field",
                params={"default_value": ""},
            )
        )
        plan.add_step(
            MigrationStep(
                operation=MigrationType.REMOVE_FIELD,
                path="properties.legacy",
                description="Remove legacy field",
            )
        )
        
        script = plan.to_script("python")
        
        assert "def migrate(data" in script
        assert "email" in script
        assert "legacy" in script
        assert "1.0" in script
        assert "2.0" in script

    def test_javascript_script_generation(self):
        """Test JavaScript migration script generation."""
        plan = MigrationPlan(source_version="1.0", target_version="2.0")
        plan.add_step(
            MigrationStep(
                operation=MigrationType.ADD_FIELD,
                path="properties.email",
                description="Add email field",
                params={"default_value": ""},
            )
        )
        
        script = plan.to_script("javascript")
        
        assert "function migrate(data)" in script
        assert "email" in script
        assert "module.exports" in script

    def test_plan_reversibility(self):
        """Test plan reversibility detection."""
        plan = MigrationPlan(source_version="1", target_version="2")
        
        # Reversible step
        plan.add_step(
            MigrationStep(
                operation=MigrationType.ADD_FIELD,
                path="x",
                description="Add",
                reversible=True,
            )
        )
        assert plan.is_reversible
        
        # Non-reversible step
        plan.add_step(
            MigrationStep(
                operation=MigrationType.REMOVE_FIELD,
                path="y",
                description="Remove",
                reversible=False,
            )
        )
        assert not plan.is_reversible

    def test_plan_warnings(self):
        """Test plan warnings for breaking changes."""
        change = SchemaChange(
            path="properties.data",
            change_type=ChangeType.REMOVED,
        )
        diff_result = DiffResult(old_version="1", new_version="2", changes=[change])
        classifier = ChangeClassifier()
        classification = classifier.classify(diff_result)
        
        strategy = MigrationStrategy()
        plan = strategy.generate(classification)
        
        # Should have warning about breaking change
        assert len(plan.warnings) > 0
        assert "Breaking" in plan.warnings[0]

    def test_custom_transformer(self):
        """Test custom value transformer."""
        strategy = MigrationStrategy()
        
        # Register custom transformer
        strategy.register_transformer("uppercase", lambda x: x.upper())
        
        plan = MigrationPlan(source_version="1", target_version="2")
        plan.add_step(
            MigrationStep(
                operation=MigrationType.TRANSFORM_VALUE,
                path="properties.name",
                description="Uppercase name",
                params={"transform": "uppercase"},
            )
        )
        
        data = {"name": "test"}
        result = strategy.execute(plan, data)
        
        assert result["name"] == "TEST"
