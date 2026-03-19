"""Compatibility validation module.

This module provides the CompatibilityValidator class for checking
backward and forward compatibility between schema versions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from jsonschema_changelog.classifier import (
    ChangeCategory,
    ClassificationResult,
    ChangeClassifier,
)
from jsonschema_changelog.diff import DiffResult, SchemaDiff


class CompatibilityLevel(Enum):
    """Levels of schema compatibility."""

    FULL = "full"  # Both backward and forward compatible
    BACKWARD = "backward"  # Old data works with new schema
    FORWARD = "forward"  # New data works with old schema
    NONE = "none"  # Neither direction compatible


@dataclass
class CompatibilityIssue:
    """A compatibility issue found during validation."""

    path: str
    issue_type: str
    description: str
    severity: str
    direction: str  # "backward", "forward", or "both"
    suggestion: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": self.path,
            "issue_type": self.issue_type,
            "description": self.description,
            "severity": self.severity,
            "direction": self.direction,
            "suggestion": self.suggestion,
            "metadata": self.metadata,
        }


@dataclass
class CompatibilityResult:
    """Result of compatibility validation."""

    old_version: str
    new_version: str
    level: CompatibilityLevel
    is_backward_compatible: bool
    is_forward_compatible: bool
    issues: List[CompatibilityIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_compatible(self) -> bool:
        """Check if schemas are compatible in any direction."""
        return self.is_backward_compatible or self.is_forward_compatible

    @property
    def is_fully_compatible(self) -> bool:
        """Check if schemas are fully compatible."""
        return self.level == CompatibilityLevel.FULL

    @property
    def issue_count(self) -> int:
        """Get the number of issues."""
        return len(self.issues)

    def get_issues_by_direction(self, direction: str) -> List[CompatibilityIssue]:
        """Get issues affecting a specific direction."""
        return [
            i for i in self.issues if i.direction == direction or i.direction == "both"
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "level": self.level.value,
            "is_backward_compatible": self.is_backward_compatible,
            "is_forward_compatible": self.is_forward_compatible,
            "issue_count": self.issue_count,
            "issues": [i.to_dict() for i in self.issues],
            "suggestions": self.suggestions,
            "metadata": self.metadata,
        }


class CompatibilityValidator:
    """Validate compatibility between schema versions.

    This class checks whether schemas are backward and/or forward
    compatible, identifying specific issues and providing suggestions.

    Backward compatibility: Data valid against old schema is valid against new schema.
    Forward compatibility: Data valid against new schema is valid against old schema.

    Example:
        >>> validator = CompatibilityValidator()
        >>> result = validator.validate(old_schema, new_schema)
        >>> if not result.is_backward_compatible:
        ...     for issue in result.issues:
        ...         print(issue.description)
    """

    def __init__(self, strict_mode: bool = False) -> None:
        """Initialize CompatibilityValidator.

        Args:
            strict_mode: If True, treat ambiguous changes as incompatible
        """
        self.strict_mode = strict_mode
        self._differ = SchemaDiff()
        self._classifier = ChangeClassifier(strict_mode=strict_mode)

    def validate(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        old_version: str = "old",
        new_version: str = "new",
    ) -> CompatibilityResult:
        """Validate compatibility between two schemas.

        Args:
            old_schema: The original schema
            new_schema: The modified schema
            old_version: Version label for old schema
            new_version: Version label for new schema

        Returns:
            CompatibilityResult with compatibility level and issues
        """
        # Get the diff and classify changes
        diff_result = self._differ.compare(
            old_schema, new_schema, old_version, new_version
        )
        classification = self._classifier.classify(diff_result)

        # Analyze compatibility
        issues: List[CompatibilityIssue] = []
        suggestions: List[str] = []

        backward_issues = self._check_backward_compatibility(classification)
        forward_issues = self._check_forward_compatibility(classification)

        issues.extend(backward_issues)
        issues.extend(forward_issues)

        # Determine compatibility level
        is_backward = len(backward_issues) == 0
        is_forward = len(forward_issues) == 0

        if is_backward and is_forward:
            level = CompatibilityLevel.FULL
        elif is_backward:
            level = CompatibilityLevel.BACKWARD
        elif is_forward:
            level = CompatibilityLevel.FORWARD
        else:
            level = CompatibilityLevel.NONE

        # Generate suggestions
        suggestions = self._generate_suggestions(issues, classification)

        return CompatibilityResult(
            old_version=old_version,
            new_version=new_version,
            level=level,
            is_backward_compatible=is_backward,
            is_forward_compatible=is_forward,
            issues=issues,
            suggestions=suggestions,
            metadata=classification.metadata.copy(),
        )

    def check_backward_compatibility(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
    ) -> bool:
        """Quick check for backward compatibility.

        Args:
            old_schema: The original schema
            new_schema: The modified schema

        Returns:
            True if backward compatible
        """
        result = self.validate(old_schema, new_schema)
        return result.is_backward_compatible

    def check_forward_compatibility(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
    ) -> bool:
        """Quick check for forward compatibility.

        Args:
            old_schema: The original schema
            new_schema: The modified schema

        Returns:
            True if forward compatible
        """
        result = self.validate(old_schema, new_schema)
        return result.is_forward_compatible

    def _check_backward_compatibility(
        self, classification: ClassificationResult
    ) -> List[CompatibilityIssue]:
        """Check for backward compatibility issues.

        Backward compatibility is broken when:
        - Required fields are added
        - Types become more restrictive
        - Enum values are removed
        - Validation constraints become stricter
        """
        issues: List[CompatibilityIssue] = []

        for change in classification.changes:
            if change.category == ChangeCategory.BREAKING:
                issue = CompatibilityIssue(
                    path=change.change.path,
                    issue_type=change.change.change_type.value,
                    description=change.impact_description,
                    severity=change.severity.value,
                    direction="backward",
                    suggestion=change.migration_hint,
                    metadata=change.change.metadata.copy(),
                )
                issues.append(issue)

        return issues

    def _check_forward_compatibility(
        self, classification: ClassificationResult
    ) -> List[CompatibilityIssue]:
        """Check for forward compatibility issues.

        Forward compatibility is broken when:
        - Required fields are removed (new data might not have them)
        - New required fields are added (old schema won't validate)
        - Types change incompatibly
        """
        issues: List[CompatibilityIssue] = []

        for change in classification.changes:
            # For forward compatibility, we need to consider different rules
            # Adding optional fields breaks forward compatibility
            # because old schema won't know about them
            
            change_type = change.change.change_type.value
            
            # Property additions can break forward compatibility
            # if old schema has additionalProperties: false
            if change_type == "added" and self.strict_mode:
                issue = CompatibilityIssue(
                    path=change.change.path,
                    issue_type="property_added",
                    description="New property added, old schema may reject",
                    severity="medium",
                    direction="forward",
                    suggestion="Ensure old schema allows additional properties",
                )
                issues.append(issue)

            # Removing required breaks forward compatibility
            if change_type == "required_removed":
                issue = CompatibilityIssue(
                    path=change.change.path,
                    issue_type="required_removed",
                    description="Required field removed, new data may omit it",
                    severity="medium",
                    direction="forward",
                    suggestion="Old code may expect this field to exist",
                )
                issues.append(issue)

            # Widening enum values breaks forward compatibility
            if change_type == "enum_added":
                issue = CompatibilityIssue(
                    path=change.change.path,
                    issue_type="enum_expanded",
                    description="New enum values added, old schema will reject",
                    severity="high",
                    direction="forward",
                    suggestion="Old validators won't accept new enum values",
                )
                issues.append(issue)

        return issues

    def _generate_suggestions(
        self,
        issues: List[CompatibilityIssue],
        classification: ClassificationResult,
    ) -> List[str]:
        """Generate migration suggestions based on issues."""
        suggestions: List[str] = []

        # Count issue types
        issue_types = {}
        for issue in issues:
            issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1

        # General suggestions
        if not classification.is_compatible:
            suggestions.append(
                "Consider using a phased rollout with both schema versions"
            )

        if issue_types.get("required_added", 0) > 0:
            suggestions.append(
                "For new required fields, provide default values in migration"
            )

        if issue_types.get("removed", 0) > 0:
            suggestions.append(
                "Mark fields as deprecated before removing them"
            )

        if issue_types.get("type_changed", 0) > 0:
            suggestions.append(
                "Consider using union types during transition period"
            )

        if issue_types.get("enum_removed", 0) > 0:
            suggestions.append(
                "Migrate existing data with removed enum values before deploying"
            )

        # Add LIMS-specific suggestions
        if any("patient" in i.path.lower() or "sample" in i.path.lower() for i in issues):
            suggestions.append(
                "Critical: Changes affect patient/sample data. "
                "Ensure compliance with data retention requirements."
            )

        return suggestions


def validate_compatibility(
    old_schema: Dict[str, Any],
    new_schema: Dict[str, Any],
    strict_mode: bool = False,
) -> CompatibilityResult:
    """Convenience function to validate compatibility.

    Args:
        old_schema: The original schema
        new_schema: The modified schema
        strict_mode: Whether to use strict validation

    Returns:
        CompatibilityResult with compatibility information
    """
    validator = CompatibilityValidator(strict_mode=strict_mode)
    return validator.validate(old_schema, new_schema)
