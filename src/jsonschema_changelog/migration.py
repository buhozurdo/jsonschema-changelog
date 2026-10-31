"""Migration strategy module.

This module provides tools for generating and executing data migrations
when schema changes occur.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from jsonschema_changelog.classifier import ChangeCategory, ClassificationResult
from jsonschema_changelog.diff import ChangeType, SchemaChange


class MigrationType(Enum):
    """Types of migration operations."""

    ADD_FIELD = "add_field"
    REMOVE_FIELD = "remove_field"
    RENAME_FIELD = "rename_field"
    TRANSFORM_VALUE = "transform_value"
    CHANGE_TYPE = "change_type"
    SET_DEFAULT = "set_default"
    CUSTOM = "custom"


@dataclass
class MigrationStep:
    """A single migration step."""

    operation: MigrationType
    path: str
    description: str
    params: Dict[str, Any] = field(default_factory=dict)
    transformer: Optional[Callable[[Any], Any]] = None
    reversible: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "operation": self.operation.value,
            "path": self.path,
            "description": self.description,
            "params": self.params,
            "reversible": self.reversible,
            "metadata": self.metadata,
        }


@dataclass
class MigrationPlan:
    """A complete migration plan with ordered steps."""

    source_version: str
    target_version: str
    steps: List[MigrationStep] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_reversible(self) -> bool:
        """Check if all steps are reversible."""
        return all(step.reversible for step in self.steps)

    @property
    def step_count(self) -> int:
        """Get the number of steps."""
        return len(self.steps)

    def add_step(self, step: MigrationStep) -> None:
        """Add a migration step."""
        self.steps.append(step)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "source_version": self.source_version,
            "target_version": self.target_version,
            "is_reversible": self.is_reversible,
            "step_count": self.step_count,
            "steps": [s.to_dict() for s in self.steps],
            "warnings": self.warnings,
            "metadata": self.metadata,
        }

    def to_script(self, language: str = "python") -> str:
        """Generate migration script."""
        if language == "python":
            return self._generate_python_script()
        elif language == "javascript":
            return self._generate_javascript_script()
        else:
            raise ValueError(f"Unsupported language: {language}")

    def _generate_python_script(self) -> str:
        """Generate Python migration script."""
        lines = [
            '"""',
            f"Migration: {self.source_version} -> {self.target_version}",
            f"Steps: {self.step_count}",
            f"Reversible: {self.is_reversible}",
            '"""',
            "",
            "from typing import Any, Dict",
            "",
            "",
            "def migrate(data: Dict[str, Any]) -> Dict[str, Any]:",
            '    """Migrate data from source to target schema version."""',
            "    result = data.copy()",
            "",
        ]

        for i, step in enumerate(self.steps, 1):
            lines.append(f"    # Step {i}: {step.description}")
            lines.extend(self._generate_python_step(step))
            lines.append("")

        lines.extend([
            "    return result",
            "",
            "",
            'if __name__ == "__main__":',
            "    import json",
            "    import sys",
            "",
            "    if len(sys.argv) < 2:",
            '        print("Usage: python migrate.py <input.json>")',
            "        sys.exit(1)",
            "",
            '    with open(sys.argv[1], "r") as f:',
            "        data = json.load(f)",
            "",
            "    migrated = migrate(data)",
            "    print(json.dumps(migrated, indent=2))",
        ])

        return "\n".join(lines)

    def _python_transform_value(self, path_key: str, step: MigrationStep) -> List[str]:
        """Generate Python code for a transform value step."""
        transform_type = step.params.get("transform", "identity")
        if transform_type == "to_string":
            return [
                f'    if "{path_key}" in result:',
                f'        result["{path_key}"] = str(result["{path_key}"])',
            ]
        elif transform_type == "to_integer":
            return [
                f'    if "{path_key}" in result:',
                f'        result["{path_key}"] = int(result["{path_key}"])',
            ]
        return [
            f"    # TODO: Implement custom transform for {path_key}",
            f'    # result["{path_key}"] = transform(result["{path_key}"])',
        ]

    def _python_change_type(self, path_key: str, step: MigrationStep) -> List[str]:
        """Generate Python code for a change type step."""
        old_type = step.params.get("old_type", "any")
        new_type = step.params.get("new_type", "any")
        lines = [
            f"    # Type change: {old_type} -> {new_type}",
            f'    if "{path_key}" in result:',
        ]
        if new_type == "string":
            lines.append(f'        result["{path_key}"] = str(result["{path_key}"])')
        elif new_type == "integer":
            lines.append(f'        result["{path_key}"] = int(result["{path_key}"])')
        elif new_type == "number":
            lines.append(f'        result["{path_key}"] = float(result["{path_key}"])')
        elif new_type == "boolean":
            lines.append(f'        result["{path_key}"] = bool(result["{path_key}"])')
        else:
            lines.extend([
                f"        # TODO: Handle conversion to {new_type}",
                "        pass",
            ])
        return lines

    def _generate_python_step(self, step: MigrationStep) -> List[str]:
        """Generate Python code for a migration step."""
        lines: List[str] = []
        path_parts = step.path.split(".")
        path_key = path_parts[-1] if path_parts else step.path

        if step.operation == MigrationType.ADD_FIELD:
            default_value = step.params.get("default_value", "None")
            lines.extend([
                f'    if "{path_key}" not in result:',
                f'        result["{path_key}"] = {repr(default_value)}',
            ])

        elif step.operation == MigrationType.REMOVE_FIELD:
            lines.extend([
                f'    if "{path_key}" in result:',
                f'        del result["{path_key}"]',
            ])

        elif step.operation == MigrationType.RENAME_FIELD:
            new_name = step.params.get("new_name", f"{path_key}_new")
            lines.extend([
                f'    if "{path_key}" in result:',
                f'        result["{new_name}"] = result.pop("{path_key}")',
            ])

        elif step.operation == MigrationType.TRANSFORM_VALUE:
            lines.extend(self._python_transform_value(path_key, step))

        elif step.operation == MigrationType.CHANGE_TYPE:
            lines.extend(self._python_change_type(path_key, step))

        elif step.operation == MigrationType.SET_DEFAULT:
            default_value = step.params.get("default_value")
            lines.extend([
                f'    if "{path_key}" not in result or result["{path_key}"] is None:',
                f'        result["{path_key}"] = {repr(default_value)}',
            ])

        elif step.operation == MigrationType.CUSTOM:
            lines.extend([
                f"    # Custom migration for {step.path}",
                "    # TODO: Implement custom migration logic",
                "    pass",
            ])

        return lines

    def _generate_javascript_script(self) -> str:
        """Generate JavaScript migration script."""
        lines = [
            "/**",
            f" * Migration: {self.source_version} -> {self.target_version}",
            f" * Steps: {self.step_count}",
            f" * Reversible: {self.is_reversible}",
            " */",
            "",
            "function migrate(data) {",
            "  const result = { ...data };",
            "",
        ]

        for i, step in enumerate(self.steps, 1):
            lines.append(f"  // Step {i}: {step.description}")
            lines.extend(self._generate_javascript_step(step))
            lines.append("")

        lines.extend([
            "  return result;",
            "}",
            "",
            "module.exports = { migrate };",
        ])

        return "\n".join(lines)

    def _generate_javascript_step(self, step: MigrationStep) -> List[str]:
        """Generate JavaScript code for a migration step."""
        lines: List[str] = []
        path_parts = step.path.split(".")
        path_key = path_parts[-1] if path_parts else step.path

        if step.operation == MigrationType.ADD_FIELD:
            default_value = step.params.get("default_value", "null")
            js_value = "null" if default_value is None else repr(default_value)
            lines.extend([
                f'  if (result["{path_key}"] === undefined) {{',
                f'    result["{path_key}"] = {js_value};',
                "  }",
            ])

        elif step.operation == MigrationType.REMOVE_FIELD:
            lines.append(f'  delete result["{path_key}"];')

        elif step.operation == MigrationType.RENAME_FIELD:
            new_name = step.params.get("new_name", f"{path_key}_new")
            lines.extend([
                f'  if ("{path_key}" in result) {{',
                f'    result["{new_name}"] = result["{path_key}"];',
                f'    delete result["{path_key}"];',
                "  }",
            ])

        elif step.operation == MigrationType.CHANGE_TYPE:
            new_type = step.params.get("new_type", "any")
            lines.append(f'  if ("{path_key}" in result) {{')
            if new_type == "string":
                lines.append(
                    f'    result["{path_key}"] = String(result["{path_key}"]);'
                )
            elif new_type in ("integer", "number"):
                lines.append(
                    f'    result["{path_key}"] = Number(result["{path_key}"]);'
                )
            elif new_type == "boolean":
                lines.append(
                    f'    result["{path_key}"] = Boolean(result["{path_key}"]);'
                )
            else:
                lines.append(f"    // TODO: Handle conversion to {new_type}")
            lines.append("  }")

        else:
            lines.append(f"  // TODO: Implement {step.operation.value} for {path_key}")

        return lines


class MigrationStrategy:
    """Generate migration strategies from schema changes.

    This class analyzes schema changes and generates migration plans
    that can be executed to transform data from old to new schema.

    Example:
        >>> strategy = MigrationStrategy()
        >>> plan = strategy.generate(classification_result)
        >>> script = plan.to_script("python")

    """

    def __init__(self) -> None:
        """Initialize MigrationStrategy."""
        self._transformers: Dict[str, Callable[[Any], Any]] = {}

    def register_transformer(
        self, name: str, transformer: Callable[[Any], Any]
    ) -> None:
        """Register a custom value transformer."""
        self._transformers[name] = transformer

    def generate(
        self,
        classification_result: ClassificationResult,
    ) -> MigrationPlan:
        """Generate a migration plan from classified changes.

        Args:
            classification_result: The classified schema changes

        Returns:
            MigrationPlan with steps to migrate data

        """
        plan = MigrationPlan(
            source_version=classification_result.old_version,
            target_version=classification_result.new_version,
            metadata=classification_result.metadata.copy(),
        )

        for classified_change in classification_result.changes:
            change = classified_change.change
            steps = self._generate_steps(change, classified_change.category)

            for step in steps:
                plan.add_step(step)

            # Add warnings for breaking changes
            if classified_change.category == ChangeCategory.BREAKING:
                plan.add_warning(
                    f"Breaking change at '{change.path}': "
                    f"{classified_change.impact_description}"
                )

        return plan

    def _generate_steps(
        self, change: SchemaChange, category: ChangeCategory
    ) -> List[MigrationStep]:
        """Generate migration steps for a single change."""
        steps: List[MigrationStep] = []

        if change.change_type == ChangeType.ADDED:
            # New field added - set default value
            steps.append(
                MigrationStep(
                    operation=MigrationType.ADD_FIELD,
                    path=change.path,
                    description=f"Add new field '{change.path}'",
                    params={"default_value": self._get_default_value(change.new_value)},
                )
            )

        elif change.change_type == ChangeType.REMOVED:
            # Field removed - optionally remove from data
            steps.append(
                MigrationStep(
                    operation=MigrationType.REMOVE_FIELD,
                    path=change.path,
                    description=f"Remove field '{change.path}'",
                    reversible=False,  # Data loss
                )
            )

        elif change.change_type == ChangeType.TYPE_CHANGED:
            # Type changed - transform value
            steps.append(
                MigrationStep(
                    operation=MigrationType.CHANGE_TYPE,
                    path=change.path,
                    description=(
                        f"Convert type from '{change.old_value}' "
                        f"to '{change.new_value}'"
                    ),
                    params={
                        "old_type": change.old_value,
                        "new_type": change.new_value,
                    },
                    reversible=self._is_type_conversion_reversible(
                        change.old_value, change.new_value
                    ),
                )
            )

        elif change.change_type == ChangeType.REQUIRED_ADDED:
            # Field became required - ensure it has a value
            steps.append(
                MigrationStep(
                    operation=MigrationType.SET_DEFAULT,
                    path=change.path,
                    description=f"Ensure required field '{change.path}' has a value",
                    params={"default_value": self._get_field_default(change)},
                )
            )

        elif change.change_type == ChangeType.ENUM_REMOVED:
            # Enum values removed - may need to transform
            steps.append(
                MigrationStep(
                    operation=MigrationType.TRANSFORM_VALUE,
                    path=change.path,
                    description=f"Handle removed enum values at '{change.path}'",
                    params={
                        "removed_values": change.old_value,
                        "transform": "custom",
                    },
                    reversible=False,
                )
            )

        elif change.change_type == ChangeType.DEFAULT_CHANGED:
            # Default value changed - may need to update existing nulls
            steps.append(
                MigrationStep(
                    operation=MigrationType.SET_DEFAULT,
                    path=change.path,
                    description=f"Update default value at '{change.path}'",
                    params={
                        "old_default": change.old_value,
                        "new_default": change.new_value,
                    },
                )
            )

        elif change.change_type == ChangeType.CONSTRAINT_CHANGED:
            # Constraint changed - may need validation/transformation
            constraint = change.metadata.get("constraint", "")
            if category == ChangeCategory.BREAKING:
                steps.append(
                    MigrationStep(
                        operation=MigrationType.CUSTOM,
                        path=change.path,
                        description=(
                            f"Handle constraint change '{constraint}' "
                            f"at '{change.path}'"
                        ),
                        params={
                            "constraint": constraint,
                            "old_value": change.old_value,
                            "new_value": change.new_value,
                        },
                    )
                )

        return steps

    def _get_default_value(self, schema: Any) -> Any:
        """Get a reasonable default value for a schema."""
        if not isinstance(schema, dict):
            return None

        # Check for explicit default
        if "default" in schema:
            return schema["default"]

        # Infer from type
        schema_type = schema.get("type")
        if schema_type == "string":
            return ""
        elif schema_type == "integer":
            return 0
        elif schema_type == "number":
            return 0.0
        elif schema_type == "boolean":
            return False
        elif schema_type == "array":
            return []
        elif schema_type == "object":
            return {}
        elif schema_type == "null":
            return None

        return None

    def _get_field_default(self, change: SchemaChange) -> Any:
        """Get default value for a required field."""
        # Try to get from metadata
        if "default" in change.metadata:
            return change.metadata["default"]

        # Use field name to make educated guess
        field_name = change.metadata.get("field_name", change.path).lower()

        # Common field defaults for LIMS
        defaults = {
            "status": "unknown",
            "created_at": "1970-01-01T00:00:00Z",
            "updated_at": "1970-01-01T00:00:00Z",
            "version": 1,
            "active": True,
            "enabled": True,
        }

        return defaults.get(field_name)

    def _is_type_conversion_reversible(self, old_type: Any, new_type: Any) -> bool:
        """Check if a type conversion is reversible."""
        # Widening conversions are generally reversible
        reversible_pairs = {
            ("integer", "number"),
            ("integer", "string"),
            ("number", "string"),
            ("boolean", "string"),
        }

        return (old_type, new_type) in reversible_pairs

    def execute(
        self,
        plan: MigrationPlan,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a migration plan on data.

        Args:
            plan: The migration plan to execute
            data: The data to migrate

        Returns:
            Migrated data

        """
        result = data.copy()

        for step in plan.steps:
            result = self._execute_step(step, result)

        return result

    @staticmethod
    def _resolve_path_key(path: str) -> str:
        """Extract path key handling nested property paths."""
        if ".properties." in path:
            parts = path.split(".properties.")
            return parts[-1].split(".")[0]
        path_parts = path.split(".")
        return path_parts[-1] if path_parts else path

    def _apply_transform_value(self, step: MigrationStep, value: Any) -> Any:
        """Apply transformer function for TRANSFORM_VALUE step."""
        transformer_name = step.params.get("transform")
        if transformer_name in self._transformers:
            return self._transformers[transformer_name](value)
        if step.transformer:
            return step.transformer(value)
        return value

    def _execute_step(
        self,
        step: MigrationStep,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single migration step."""
        result = data.copy()
        path_key = self._resolve_path_key(step.path)

        if step.operation == MigrationType.ADD_FIELD:
            if path_key not in result:
                result[path_key] = step.params.get("default_value")

        elif step.operation == MigrationType.REMOVE_FIELD:
            if path_key in result:
                del result[path_key]

        elif step.operation == MigrationType.RENAME_FIELD:
            if path_key in result:
                new_name = step.params.get("new_name", f"{path_key}_new")
                result[new_name] = result.pop(path_key)

        elif step.operation == MigrationType.SET_DEFAULT:
            if path_key not in result or result[path_key] is None:
                result[path_key] = step.params.get("default_value")

        elif step.operation == MigrationType.CHANGE_TYPE:
            if path_key in result:
                new_type = step.params.get("new_type")
                result[path_key] = self._convert_type(result[path_key], new_type)

        elif step.operation == MigrationType.TRANSFORM_VALUE:
            if path_key in result:
                result[path_key] = self._apply_transform_value(step, result[path_key])

        return result

    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert a value to target type."""
        if target_type == "string":
            return str(value)
        elif target_type == "integer":
            return int(value)
        elif target_type == "number":
            return float(value)
        elif target_type == "boolean":
            return bool(value)
        elif target_type == "null":
            return None
        return value

    def validate_migration(
        self,
        plan: MigrationPlan,
        data: Dict[str, Any],
        target_schema: Dict[str, Any],
    ) -> bool:
        """Validate that migrated data conforms to target schema.

        Args:
            plan: The migration plan
            data: The original data
            target_schema: The target schema

        Returns:
            True if migration produces valid data

        """
        from jsonschema import ValidationError, validate

        try:
            migrated = self.execute(plan, data)
            validate(instance=migrated, schema=target_schema)
            return True
        except ValidationError:
            return False
