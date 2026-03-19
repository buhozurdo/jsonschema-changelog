"""Schema difference detection module.

This module provides the SchemaDiff class for detecting changes
between JSON Schema versions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class ChangeType(Enum):
    """Types of schema changes."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    TYPE_CHANGED = "type_changed"
    REQUIRED_ADDED = "required_added"
    REQUIRED_REMOVED = "required_removed"
    ENUM_ADDED = "enum_added"
    ENUM_REMOVED = "enum_removed"
    CONSTRAINT_CHANGED = "constraint_changed"
    DESCRIPTION_CHANGED = "description_changed"
    FORMAT_CHANGED = "format_changed"
    PATTERN_CHANGED = "pattern_changed"
    REF_CHANGED = "ref_changed"
    DEFAULT_CHANGED = "default_changed"
    DEPRECATED = "deprecated"


@dataclass
class SchemaChange:
    """Represents a single change between schema versions."""

    path: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Generate description if not provided."""
        if not self.description:
            self.description = self._generate_description()

    def _generate_description(self) -> str:
        """Generate a human-readable description of the change."""
        descriptions = {
            ChangeType.ADDED: f"Added property '{self.path}'",
            ChangeType.REMOVED: f"Removed property '{self.path}'",
            ChangeType.MODIFIED: f"Modified property '{self.path}'",
            ChangeType.TYPE_CHANGED: f"Changed type at '{self.path}' from '{self.old_value}' to '{self.new_value}'",
            ChangeType.REQUIRED_ADDED: f"Made '{self.path}' required",
            ChangeType.REQUIRED_REMOVED: f"Made '{self.path}' optional",
            ChangeType.ENUM_ADDED: f"Added enum values at '{self.path}': {self.new_value}",
            ChangeType.ENUM_REMOVED: f"Removed enum values at '{self.path}': {self.old_value}",
            ChangeType.CONSTRAINT_CHANGED: f"Changed constraint at '{self.path}'",
            ChangeType.DESCRIPTION_CHANGED: f"Updated description at '{self.path}'",
            ChangeType.FORMAT_CHANGED: f"Changed format at '{self.path}' from '{self.old_value}' to '{self.new_value}'",
            ChangeType.PATTERN_CHANGED: f"Changed pattern at '{self.path}'",
            ChangeType.REF_CHANGED: f"Changed $ref at '{self.path}'",
            ChangeType.DEFAULT_CHANGED: f"Changed default value at '{self.path}'",
            ChangeType.DEPRECATED: f"Deprecated '{self.path}'",
        }
        return descriptions.get(self.change_type, f"Changed '{self.path}'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": self.path,
            "change_type": self.change_type.value,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass
class DiffResult:
    """Result of comparing two schemas."""

    old_version: str
    new_version: str
    changes: List[SchemaChange] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return len(self.changes) > 0

    @property
    def change_count(self) -> int:
        """Get the total number of changes."""
        return len(self.changes)

    def get_changes_by_type(self, change_type: ChangeType) -> List[SchemaChange]:
        """Get all changes of a specific type."""
        return [c for c in self.changes if c.change_type == change_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "change_count": self.change_count,
            "changes": [c.to_dict() for c in self.changes],
            "metadata": self.metadata,
        }


class SchemaDiff:
    """Detect differences between JSON Schema versions.

    This class compares two JSON Schemas and identifies all changes
    including property additions/removals, type changes, constraint
    modifications, and more.

    Example:
        >>> diff = SchemaDiff()
        >>> result = diff.compare(old_schema, new_schema)
        >>> for change in result.changes:
        ...     print(change.description)
    """

    # Keywords that affect validation
    VALIDATION_KEYWORDS = {
        "type",
        "enum",
        "const",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "pattern",
        "format",
        "minItems",
        "maxItems",
        "uniqueItems",
        "minProperties",
        "maxProperties",
        "required",
        "additionalProperties",
        "items",
        "contains",
        "minContains",
        "maxContains",
        "properties",
        "patternProperties",
        "dependencies",
        "dependentRequired",
        "dependentSchemas",
        "if",
        "then",
        "else",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "$ref",
    }

    # Keywords that are documentation only
    DOCUMENTATION_KEYWORDS = {"title", "description", "examples", "$comment", "default"}

    # Constraint keywords
    CONSTRAINT_KEYWORDS = {
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "minProperties",
        "maxProperties",
    }

    def __init__(
        self,
        old_version: str = "old",
        new_version: str = "new",
        include_documentation: bool = True,
    ) -> None:
        """Initialize SchemaDiff.

        Args:
            old_version: Version label for the old schema
            new_version: Version label for the new schema
            include_documentation: Whether to include documentation changes
        """
        self.old_version = old_version
        self.new_version = new_version
        self.include_documentation = include_documentation

    def compare(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        old_version: Optional[str] = None,
        new_version: Optional[str] = None,
    ) -> DiffResult:
        """Compare two JSON schemas and return detected changes.

        Args:
            old_schema: The original schema
            new_schema: The modified schema
            old_version: Optional version override for old schema
            new_version: Optional version override for new schema

        Returns:
            DiffResult containing all detected changes
        """
        version_old = old_version or self.old_version
        version_new = new_version or self.new_version

        result = DiffResult(
            old_version=version_old,
            new_version=version_new,
            metadata={
                "old_schema_id": old_schema.get("$id", ""),
                "new_schema_id": new_schema.get("$id", ""),
            },
        )

        # Compare the schemas recursively
        self._compare_schemas(old_schema, new_schema, "", result)

        return result

    def _compare_schemas(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Recursively compare two schemas.

        Args:
            old_schema: The original schema or subschema
            new_schema: The modified schema or subschema
            path: Current path in the schema
            result: DiffResult to accumulate changes
        """
        # Handle None cases
        if old_schema is None:
            old_schema = {}
        if new_schema is None:
            new_schema = {}

        # Compare properties
        self._compare_properties(old_schema, new_schema, path, result)

        # Compare required fields
        self._compare_required(old_schema, new_schema, path, result)

        # Compare type
        self._compare_type(old_schema, new_schema, path, result)

        # Compare enum
        self._compare_enum(old_schema, new_schema, path, result)

        # Compare constraints
        self._compare_constraints(old_schema, new_schema, path, result)

        # Compare format
        self._compare_format(old_schema, new_schema, path, result)

        # Compare pattern
        self._compare_pattern(old_schema, new_schema, path, result)

        # Compare $ref
        self._compare_ref(old_schema, new_schema, path, result)

        # Compare items (for arrays)
        self._compare_items(old_schema, new_schema, path, result)

        # Compare additionalProperties
        self._compare_additional_properties(old_schema, new_schema, path, result)

        # Compare definitions/$defs
        self._compare_definitions(old_schema, new_schema, path, result)

        # Compare documentation (if enabled)
        if self.include_documentation:
            self._compare_documentation(old_schema, new_schema, path, result)

        # Check for deprecation
        self._check_deprecation(old_schema, new_schema, path, result)

    def _compare_properties(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare properties between schemas."""
        old_props = old_schema.get("properties", {})
        new_props = new_schema.get("properties", {})

        old_keys = set(old_props.keys())
        new_keys = set(new_props.keys())

        # Added properties
        for key in new_keys - old_keys:
            prop_path = f"{path}.properties.{key}" if path else f"properties.{key}"
            result.changes.append(
                SchemaChange(
                    path=prop_path,
                    change_type=ChangeType.ADDED,
                    new_value=new_props[key],
                    metadata={"property_name": key},
                )
            )

        # Removed properties
        for key in old_keys - new_keys:
            prop_path = f"{path}.properties.{key}" if path else f"properties.{key}"
            result.changes.append(
                SchemaChange(
                    path=prop_path,
                    change_type=ChangeType.REMOVED,
                    old_value=old_props[key],
                    metadata={"property_name": key},
                )
            )

        # Modified properties (recursively compare)
        for key in old_keys & new_keys:
            prop_path = f"{path}.properties.{key}" if path else f"properties.{key}"
            self._compare_schemas(old_props[key], new_props[key], prop_path, result)

    def _compare_required(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare required fields."""
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))

        # Newly required fields
        for field in new_required - old_required:
            req_path = f"{path}.{field}" if path else field
            result.changes.append(
                SchemaChange(
                    path=req_path,
                    change_type=ChangeType.REQUIRED_ADDED,
                    new_value=True,
                    metadata={"field_name": field},
                )
            )

        # No longer required fields
        for field in old_required - new_required:
            req_path = f"{path}.{field}" if path else field
            result.changes.append(
                SchemaChange(
                    path=req_path,
                    change_type=ChangeType.REQUIRED_REMOVED,
                    old_value=True,
                    metadata={"field_name": field},
                )
            )

    def _compare_type(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare type definitions."""
        old_type = old_schema.get("type")
        new_type = new_schema.get("type")

        if old_type != new_type and (old_type is not None or new_type is not None):
            result.changes.append(
                SchemaChange(
                    path=path or "root",
                    change_type=ChangeType.TYPE_CHANGED,
                    old_value=old_type,
                    new_value=new_type,
                )
            )

    def _compare_enum(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare enum values."""
        old_enum = old_schema.get("enum")
        new_enum = new_schema.get("enum")

        if old_enum is None and new_enum is None:
            return

        if old_enum is not None and new_enum is not None:
            old_set = set(str(v) for v in old_enum)
            new_set = set(str(v) for v in new_enum)

            # Added enum values
            added = new_set - old_set
            if added:
                result.changes.append(
                    SchemaChange(
                        path=path or "root",
                        change_type=ChangeType.ENUM_ADDED,
                        new_value=list(added),
                    )
                )

            # Removed enum values
            removed = old_set - new_set
            if removed:
                result.changes.append(
                    SchemaChange(
                        path=path or "root",
                        change_type=ChangeType.ENUM_REMOVED,
                        old_value=list(removed),
                    )
                )
        elif old_enum is not None:
            # Enum removed entirely
            result.changes.append(
                SchemaChange(
                    path=path or "root",
                    change_type=ChangeType.MODIFIED,
                    old_value={"enum": old_enum},
                    new_value=None,
                    description=f"Removed enum constraint at '{path or 'root'}'",
                )
            )
        else:
            # Enum added
            result.changes.append(
                SchemaChange(
                    path=path or "root",
                    change_type=ChangeType.MODIFIED,
                    old_value=None,
                    new_value={"enum": new_enum},
                    description=f"Added enum constraint at '{path or 'root'}'",
                )
            )

    def _compare_constraints(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare constraint keywords."""
        for keyword in self.CONSTRAINT_KEYWORDS:
            old_value = old_schema.get(keyword)
            new_value = new_schema.get(keyword)

            if old_value != new_value and (
                old_value is not None or new_value is not None
            ):
                result.changes.append(
                    SchemaChange(
                        path=path or "root",
                        change_type=ChangeType.CONSTRAINT_CHANGED,
                        old_value=old_value,
                        new_value=new_value,
                        metadata={"constraint": keyword},
                        description=f"Changed '{keyword}' at '{path or 'root'}' from {old_value} to {new_value}",
                    )
                )

    def _compare_format(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare format specifications."""
        old_format = old_schema.get("format")
        new_format = new_schema.get("format")

        if old_format != new_format and (
            old_format is not None or new_format is not None
        ):
            result.changes.append(
                SchemaChange(
                    path=path or "root",
                    change_type=ChangeType.FORMAT_CHANGED,
                    old_value=old_format,
                    new_value=new_format,
                )
            )

    def _compare_pattern(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare pattern specifications."""
        old_pattern = old_schema.get("pattern")
        new_pattern = new_schema.get("pattern")

        if old_pattern != new_pattern and (
            old_pattern is not None or new_pattern is not None
        ):
            result.changes.append(
                SchemaChange(
                    path=path or "root",
                    change_type=ChangeType.PATTERN_CHANGED,
                    old_value=old_pattern,
                    new_value=new_pattern,
                )
            )

    def _compare_ref(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare $ref specifications."""
        old_ref = old_schema.get("$ref")
        new_ref = new_schema.get("$ref")

        if old_ref != new_ref and (old_ref is not None or new_ref is not None):
            result.changes.append(
                SchemaChange(
                    path=path or "root",
                    change_type=ChangeType.REF_CHANGED,
                    old_value=old_ref,
                    new_value=new_ref,
                )
            )

    def _compare_items(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare items specifications for arrays."""
        old_items = old_schema.get("items")
        new_items = new_schema.get("items")

        if old_items is None and new_items is None:
            return

        items_path = f"{path}.items" if path else "items"

        if isinstance(old_items, dict) and isinstance(new_items, dict):
            self._compare_schemas(old_items, new_items, items_path, result)
        elif old_items != new_items:
            result.changes.append(
                SchemaChange(
                    path=items_path,
                    change_type=ChangeType.MODIFIED,
                    old_value=old_items,
                    new_value=new_items,
                    description=f"Changed items schema at '{items_path}'",
                )
            )

    def _compare_additional_properties(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare additionalProperties specifications."""
        old_additional = old_schema.get("additionalProperties")
        new_additional = new_schema.get("additionalProperties")

        if old_additional == new_additional:
            return

        if old_additional is None and new_additional is None:
            return

        add_path = (
            f"{path}.additionalProperties" if path else "additionalProperties"
        )

        if isinstance(old_additional, dict) and isinstance(new_additional, dict):
            self._compare_schemas(old_additional, new_additional, add_path, result)
        else:
            result.changes.append(
                SchemaChange(
                    path=add_path,
                    change_type=ChangeType.MODIFIED,
                    old_value=old_additional,
                    new_value=new_additional,
                    description=f"Changed additionalProperties at '{add_path}'",
                )
            )

    def _compare_definitions(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare definitions/$defs."""
        # Check both definitions (Draft 7) and $defs (Draft 2019-09+)
        for defs_key in ["definitions", "$defs"]:
            old_defs = old_schema.get(defs_key, {})
            new_defs = new_schema.get(defs_key, {})

            old_keys = set(old_defs.keys())
            new_keys = set(new_defs.keys())

            defs_path = f"{path}.{defs_key}" if path else defs_key

            # Added definitions
            for key in new_keys - old_keys:
                def_path = f"{defs_path}.{key}"
                result.changes.append(
                    SchemaChange(
                        path=def_path,
                        change_type=ChangeType.ADDED,
                        new_value=new_defs[key],
                        metadata={"definition_name": key},
                    )
                )

            # Removed definitions
            for key in old_keys - new_keys:
                def_path = f"{defs_path}.{key}"
                result.changes.append(
                    SchemaChange(
                        path=def_path,
                        change_type=ChangeType.REMOVED,
                        old_value=old_defs[key],
                        metadata={"definition_name": key},
                    )
                )

            # Modified definitions
            for key in old_keys & new_keys:
                def_path = f"{defs_path}.{key}"
                self._compare_schemas(old_defs[key], new_defs[key], def_path, result)

    def _compare_documentation(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Compare documentation fields."""
        for keyword in ["title", "description"]:
            old_value = old_schema.get(keyword)
            new_value = new_schema.get(keyword)

            if old_value != new_value and (
                old_value is not None or new_value is not None
            ):
                result.changes.append(
                    SchemaChange(
                        path=path or "root",
                        change_type=ChangeType.DESCRIPTION_CHANGED,
                        old_value=old_value,
                        new_value=new_value,
                        metadata={"field": keyword},
                        description=f"Changed {keyword} at '{path or 'root'}'",
                    )
                )

        # Check default value
        old_default = old_schema.get("default")
        new_default = new_schema.get("default")

        if old_default != new_default and (
            old_default is not None or new_default is not None
        ):
            result.changes.append(
                SchemaChange(
                    path=path or "root",
                    change_type=ChangeType.DEFAULT_CHANGED,
                    old_value=old_default,
                    new_value=new_default,
                )
            )

    def _check_deprecation(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        path: str,
        result: DiffResult,
    ) -> None:
        """Check if a field was marked as deprecated."""
        old_deprecated = old_schema.get("deprecated", False)
        new_deprecated = new_schema.get("deprecated", False)

        if not old_deprecated and new_deprecated:
            result.changes.append(
                SchemaChange(
                    path=path or "root",
                    change_type=ChangeType.DEPRECATED,
                    old_value=False,
                    new_value=True,
                )
            )

        # Also check for deprecation markers in description
        old_desc = old_schema.get("description", "")
        new_desc = new_schema.get("description", "")

        deprecation_markers = ["deprecated", "obsolete", "will be removed"]
        old_has_marker = any(m in old_desc.lower() for m in deprecation_markers)
        new_has_marker = any(m in new_desc.lower() for m in deprecation_markers)

        if not old_has_marker and new_has_marker:
            result.changes.append(
                SchemaChange(
                    path=path or "root",
                    change_type=ChangeType.DEPRECATED,
                    new_value=new_desc,
                    metadata={"source": "description"},
                )
            )
