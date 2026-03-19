"""Change classification module.

This module provides the ChangeClassifier class for categorizing
schema changes as breaking, non-breaking, or deprecations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from jsonschema_changelog.diff import ChangeType, DiffResult, SchemaChange


class ChangeCategory(Enum):
    """Categories of schema changes by impact."""

    BREAKING = "breaking"
    NON_BREAKING = "non_breaking"
    DEPRECATION = "deprecation"
    DOCUMENTATION = "documentation"


class Severity(Enum):
    """Severity levels for changes."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ClassifiedChange:
    """A change with its classification."""

    change: SchemaChange
    category: ChangeCategory
    severity: Severity
    impact_description: str
    migration_hint: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": self.change.path,
            "change_type": self.change.change_type.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.change.description,
            "impact": self.impact_description,
            "migration_hint": self.migration_hint,
            "old_value": self.change.old_value,
            "new_value": self.change.new_value,
            "metadata": {**self.change.metadata, **self.metadata},
        }


@dataclass
class ClassificationResult:
    """Result of classifying changes."""

    old_version: str
    new_version: str
    changes: List[ClassifiedChange] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    is_compatible: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Calculate summary after initialization."""
        self._update_summary()

    def _update_summary(self) -> None:
        """Update the summary counts."""
        self.summary = {
            "breaking": 0,
            "non_breaking": 0,
            "deprecation": 0,
            "documentation": 0,
            "total": len(self.changes),
        }
        for change in self.changes:
            self.summary[change.category.value] += 1

        self.is_compatible = self.summary["breaking"] == 0

    @property
    def breaking_changes(self) -> List[ClassifiedChange]:
        """Get all breaking changes."""
        return [c for c in self.changes if c.category == ChangeCategory.BREAKING]

    @property
    def non_breaking_changes(self) -> List[ClassifiedChange]:
        """Get all non-breaking changes."""
        return [c for c in self.changes if c.category == ChangeCategory.NON_BREAKING]

    @property
    def deprecations(self) -> List[ClassifiedChange]:
        """Get all deprecations."""
        return [c for c in self.changes if c.category == ChangeCategory.DEPRECATION]

    @property
    def documentation_changes(self) -> List[ClassifiedChange]:
        """Get all documentation changes."""
        return [c for c in self.changes if c.category == ChangeCategory.DOCUMENTATION]

    def add_change(self, change: ClassifiedChange) -> None:
        """Add a classified change and update summary."""
        self.changes.append(change)
        self._update_summary()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "is_compatible": self.is_compatible,
            "summary": self.summary,
            "changes": [c.to_dict() for c in self.changes],
            "metadata": self.metadata,
        }


class ChangeClassifier:
    """Classify schema changes by their impact.

    This class analyzes schema changes and categorizes them as:
    - BREAKING: Changes that break backward compatibility
    - NON_BREAKING: Changes that maintain compatibility
    - DEPRECATION: Changes that mark features as deprecated
    - DOCUMENTATION: Changes to documentation only

    Example:
        >>> classifier = ChangeClassifier()
        >>> result = classifier.classify(diff_result)
        >>> print(f"Breaking changes: {len(result.breaking_changes)}")
    """

    # Breaking change patterns
    BREAKING_CHANGES = {
        ChangeType.REMOVED,
        ChangeType.REQUIRED_ADDED,
        ChangeType.ENUM_REMOVED,
    }

    # Non-breaking change patterns
    NON_BREAKING_CHANGES = {
        ChangeType.ADDED,
        ChangeType.REQUIRED_REMOVED,
        ChangeType.ENUM_ADDED,
    }

    # Documentation-only changes
    DOCUMENTATION_CHANGES = {
        ChangeType.DESCRIPTION_CHANGED,
    }

    def __init__(self, strict_mode: bool = False) -> None:
        """Initialize ChangeClassifier.

        Args:
            strict_mode: If True, treat ambiguous changes as breaking
        """
        self.strict_mode = strict_mode

    def classify(self, diff_result: DiffResult) -> ClassificationResult:
        """Classify all changes in a diff result.

        Args:
            diff_result: The diff result to classify

        Returns:
            ClassificationResult with all classified changes
        """
        result = ClassificationResult(
            old_version=diff_result.old_version,
            new_version=diff_result.new_version,
            metadata=diff_result.metadata.copy(),
        )

        for change in diff_result.changes:
            classified = self._classify_change(change)
            result.add_change(classified)

        return result

    def _classify_change(self, change: SchemaChange) -> ClassifiedChange:
        """Classify a single change.

        Args:
            change: The schema change to classify

        Returns:
            ClassifiedChange with category and severity
        """
        # Check for deprecation first
        if change.change_type == ChangeType.DEPRECATED:
            return self._create_deprecation(change)

        # Check for documentation-only changes
        if change.change_type in self.DOCUMENTATION_CHANGES:
            return self._create_documentation_change(change)

        # Check for clearly breaking changes
        if change.change_type in self.BREAKING_CHANGES:
            return self._create_breaking_change(change)

        # Check for clearly non-breaking changes
        if change.change_type in self.NON_BREAKING_CHANGES:
            return self._create_non_breaking_change(change)

        # Handle type changes
        if change.change_type == ChangeType.TYPE_CHANGED:
            return self._classify_type_change(change)

        # Handle constraint changes
        if change.change_type == ChangeType.CONSTRAINT_CHANGED:
            return self._classify_constraint_change(change)

        # Handle format changes
        if change.change_type == ChangeType.FORMAT_CHANGED:
            return self._classify_format_change(change)

        # Handle pattern changes
        if change.change_type == ChangeType.PATTERN_CHANGED:
            return self._classify_pattern_change(change)

        # Handle $ref changes
        if change.change_type == ChangeType.REF_CHANGED:
            return self._classify_ref_change(change)

        # Handle default value changes
        if change.change_type == ChangeType.DEFAULT_CHANGED:
            return self._create_non_breaking_change(
                change,
                impact="Default value changed, existing data unaffected",
            )

        # Handle general modifications
        if change.change_type == ChangeType.MODIFIED:
            return self._classify_modification(change)

        # Default: treat as non-breaking unless in strict mode
        if self.strict_mode:
            return self._create_breaking_change(
                change,
                impact="Unknown change type, treated as breaking in strict mode",
            )
        return self._create_non_breaking_change(
            change,
            impact="Change classified as non-breaking by default",
        )

    def _create_breaking_change(
        self,
        change: SchemaChange,
        impact: Optional[str] = None,
        severity: Severity = Severity.HIGH,
    ) -> ClassifiedChange:
        """Create a breaking change classification."""
        impact_descriptions = {
            ChangeType.REMOVED: "Property removed, existing data may be invalid",
            ChangeType.REQUIRED_ADDED: "Field now required, existing data missing this field will fail validation",
            ChangeType.ENUM_REMOVED: "Allowed values reduced, existing data with removed values will fail",
            ChangeType.TYPE_CHANGED: "Type changed, existing data may not validate",
        }

        migration_hints = {
            ChangeType.REMOVED: "Add data migration to handle or remove this field from existing data",
            ChangeType.REQUIRED_ADDED: "Ensure all existing data has a value for this field before migration",
            ChangeType.ENUM_REMOVED: "Update existing data to use valid enum values",
            ChangeType.TYPE_CHANGED: "Transform existing data to match the new type",
        }

        return ClassifiedChange(
            change=change,
            category=ChangeCategory.BREAKING,
            severity=severity,
            impact_description=impact
            or impact_descriptions.get(change.change_type, "Breaking change detected"),
            migration_hint=migration_hints.get(
                change.change_type, "Manual migration required"
            ),
        )

    def _create_non_breaking_change(
        self,
        change: SchemaChange,
        impact: Optional[str] = None,
        severity: Severity = Severity.LOW,
    ) -> ClassifiedChange:
        """Create a non-breaking change classification."""
        impact_descriptions = {
            ChangeType.ADDED: "New optional property added, existing data remains valid",
            ChangeType.REQUIRED_REMOVED: "Field no longer required, existing data remains valid",
            ChangeType.ENUM_ADDED: "New allowed values added, existing data remains valid",
        }

        return ClassifiedChange(
            change=change,
            category=ChangeCategory.NON_BREAKING,
            severity=severity,
            impact_description=impact
            or impact_descriptions.get(
                change.change_type, "Non-breaking change, backward compatible"
            ),
            migration_hint="No migration required",
        )

    def _create_deprecation(
        self,
        change: SchemaChange,
        severity: Severity = Severity.MEDIUM,
    ) -> ClassifiedChange:
        """Create a deprecation classification."""
        return ClassifiedChange(
            change=change,
            category=ChangeCategory.DEPRECATION,
            severity=severity,
            impact_description="Feature marked as deprecated, plan for removal",
            migration_hint="Update usage to use recommended alternative before removal",
        )

    def _create_documentation_change(
        self,
        change: SchemaChange,
        severity: Severity = Severity.INFO,
    ) -> ClassifiedChange:
        """Create a documentation change classification."""
        return ClassifiedChange(
            change=change,
            category=ChangeCategory.DOCUMENTATION,
            severity=severity,
            impact_description="Documentation updated, no functional impact",
            migration_hint="No action required",
        )

    def _classify_type_change(self, change: SchemaChange) -> ClassifiedChange:
        """Classify a type change based on type compatibility."""
        old_type = change.old_value
        new_type = change.new_value

        # Widening type changes (non-breaking)
        widening_changes = {
            ("integer", "number"),  # integer -> number is widening
            (None, "string"),  # Adding type where none existed
        }

        # Check if this is a widening change
        if (old_type, new_type) in widening_changes:
            return self._create_non_breaking_change(
                change,
                impact=f"Type widened from '{old_type}' to '{new_type}', existing data remains valid",
                severity=Severity.LOW,
            )

        # Check for array of types (union types)
        if isinstance(new_type, list) and old_type in new_type:
            return self._create_non_breaking_change(
                change,
                impact="Type expanded to union, original type still allowed",
                severity=Severity.LOW,
            )

        # Check for adding null to type
        if isinstance(new_type, list) and "null" in new_type:
            old_types = [old_type] if isinstance(old_type, str) else (old_type or [])
            if all(t in new_type for t in old_types if t != "null"):
                return self._create_non_breaking_change(
                    change,
                    impact="Null added to allowed types, existing data remains valid",
                    severity=Severity.LOW,
                )

        # Narrowing type changes are breaking
        return self._create_breaking_change(
            change,
            impact=f"Type changed from '{old_type}' to '{new_type}', existing data may be invalid",
            severity=Severity.CRITICAL,
        )

    def _classify_constraint_change(self, change: SchemaChange) -> ClassifiedChange:
        """Classify a constraint change based on whether it's more or less restrictive."""
        constraint = change.metadata.get("constraint", "")
        old_value = change.old_value
        new_value = change.new_value

        # Constraints that are breaking when increased
        increasing_constraints = {"minLength", "minItems", "minProperties", "minimum"}

        # Constraints that are breaking when decreased
        decreasing_constraints = {"maxLength", "maxItems", "maxProperties", "maximum"}

        if constraint in increasing_constraints:
            # Making minimum constraints higher is breaking
            if old_value is not None and new_value is not None:
                if new_value > old_value:
                    return self._create_breaking_change(
                        change,
                        impact=f"Minimum constraint '{constraint}' increased from {old_value} to {new_value}",
                        severity=Severity.HIGH,
                    )
                else:
                    return self._create_non_breaking_change(
                        change,
                        impact=f"Minimum constraint '{constraint}' decreased from {old_value} to {new_value}",
                        severity=Severity.LOW,
                    )
            elif old_value is None and new_value is not None:
                # Adding a minimum constraint
                return self._create_breaking_change(
                    change,
                    impact=f"Added minimum constraint '{constraint}' = {new_value}",
                    severity=Severity.HIGH,
                )
            else:
                # Removing a minimum constraint
                return self._create_non_breaking_change(
                    change,
                    impact=f"Removed minimum constraint '{constraint}'",
                    severity=Severity.LOW,
                )

        if constraint in decreasing_constraints:
            # Making maximum constraints lower is breaking
            if old_value is not None and new_value is not None:
                if new_value < old_value:
                    return self._create_breaking_change(
                        change,
                        impact=f"Maximum constraint '{constraint}' decreased from {old_value} to {new_value}",
                        severity=Severity.HIGH,
                    )
                else:
                    return self._create_non_breaking_change(
                        change,
                        impact=f"Maximum constraint '{constraint}' increased from {old_value} to {new_value}",
                        severity=Severity.LOW,
                    )
            elif old_value is None and new_value is not None:
                # Adding a maximum constraint
                return self._create_breaking_change(
                    change,
                    impact=f"Added maximum constraint '{constraint}' = {new_value}",
                    severity=Severity.HIGH,
                )
            else:
                # Removing a maximum constraint
                return self._create_non_breaking_change(
                    change,
                    impact=f"Removed maximum constraint '{constraint}'",
                    severity=Severity.LOW,
                )

        # Exclusive constraints
        if constraint.startswith("exclusive"):
            # Similar logic for exclusive constraints
            if "Min" in constraint:
                if old_value is not None and new_value is not None and new_value > old_value:
                    return self._create_breaking_change(change)
            elif "Max" in constraint:
                if old_value is not None and new_value is not None and new_value < old_value:
                    return self._create_breaking_change(change)

        # Default: treat as potentially breaking in strict mode
        if self.strict_mode:
            return self._create_breaking_change(
                change,
                impact=f"Constraint '{constraint}' changed, may affect validation",
            )
        return self._create_non_breaking_change(
            change,
            impact=f"Constraint '{constraint}' changed",
            severity=Severity.MEDIUM,
        )

    def _classify_format_change(self, change: SchemaChange) -> ClassifiedChange:
        """Classify a format change."""
        old_format = change.old_value
        new_format = change.new_value

        # Adding a format is potentially breaking (more restrictive)
        if old_format is None and new_format is not None:
            return self._create_breaking_change(
                change,
                impact=f"Format constraint '{new_format}' added, existing data may not match",
                severity=Severity.MEDIUM,
            )

        # Removing a format is non-breaking (less restrictive)
        if old_format is not None and new_format is None:
            return self._create_non_breaking_change(
                change,
                impact=f"Format constraint '{old_format}' removed, validation relaxed",
            )

        # Changing format is potentially breaking
        return self._create_breaking_change(
            change,
            impact=f"Format changed from '{old_format}' to '{new_format}'",
            severity=Severity.MEDIUM,
        )

    def _classify_pattern_change(self, change: SchemaChange) -> ClassifiedChange:
        """Classify a pattern change."""
        old_pattern = change.old_value
        new_pattern = change.new_value

        # Adding a pattern is breaking
        if old_pattern is None and new_pattern is not None:
            return self._create_breaking_change(
                change,
                impact=f"Pattern constraint added, existing data may not match",
                severity=Severity.HIGH,
            )

        # Removing a pattern is non-breaking
        if old_pattern is not None and new_pattern is None:
            return self._create_non_breaking_change(
                change,
                impact="Pattern constraint removed, validation relaxed",
            )

        # Changing pattern - need to analyze if new pattern is more or less restrictive
        # For now, treat as potentially breaking
        return self._create_breaking_change(
            change,
            impact="Pattern changed, existing data may not match new pattern",
            severity=Severity.MEDIUM,
        )

    def _classify_ref_change(self, change: SchemaChange) -> ClassifiedChange:
        """Classify a $ref change."""
        # $ref changes are generally breaking as they change the entire schema
        return self._create_breaking_change(
            change,
            impact="Schema reference changed, may affect validation",
            severity=Severity.HIGH,
        )

    def _classify_modification(self, change: SchemaChange) -> ClassifiedChange:
        """Classify a general modification."""
        description = change.description.lower()

        # Check for additionalProperties changes
        if "additionalproperties" in description:
            old_val = change.old_value
            new_val = change.new_value

            # True -> False is breaking
            if old_val is True and new_val is False:
                return self._create_breaking_change(
                    change,
                    impact="Additional properties disallowed, existing data with extra properties will fail",
                    severity=Severity.HIGH,
                )

            # False -> True is non-breaking
            if old_val is False and new_val is True:
                return self._create_non_breaking_change(
                    change,
                    impact="Additional properties now allowed",
                )

        # Check for items changes
        if "items" in description:
            # Items schema changes need careful analysis
            if self.strict_mode:
                return self._create_breaking_change(
                    change,
                    impact="Array items schema changed",
                )
            return ClassifiedChange(
                change=change,
                category=ChangeCategory.NON_BREAKING,
                severity=Severity.MEDIUM,
                impact_description="Array items schema changed, review for compatibility",
                migration_hint="Verify existing array data matches new items schema",
            )

        # Default
        if self.strict_mode:
            return self._create_breaking_change(change)
        return self._create_non_breaking_change(
            change,
            severity=Severity.MEDIUM,
        )


def classify_changes(
    diff_result: DiffResult, strict_mode: bool = False
) -> ClassificationResult:
    """Convenience function to classify changes.

    Args:
        diff_result: The diff result to classify
        strict_mode: Whether to use strict classification

    Returns:
        ClassificationResult with all classified changes
    """
    classifier = ChangeClassifier(strict_mode=strict_mode)
    return classifier.classify(diff_result)
