#!/usr/bin/env python3
"""Example: Validate compatibility between schema versions.

This example demonstrates how to check backward and forward compatibility
between schema versions, useful for CI/CD integration.
"""

import sys

from jsonschema_changelog import CompatibilityValidator

# Schema versions with different compatibility levels
schema_v1 = {
    "title": "API Response v1",
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "maxLength": 100},
        "status": {"type": "string", "enum": ["active", "inactive"]},
        "legacy_field": {"type": "string"},
    },
    "required": ["id", "name"],
}

# v2: Backward compatible (adds optional fields, expands enums)
schema_v2_compatible = {
    "title": "API Response v2",
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "maxLength": 200},  # Increased limit
        "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
        "legacy_field": {"type": "string", "deprecated": True},
        "email": {"type": "string", "format": "email"},  # New optional
    },
    "required": ["id", "name"],
}

# v3: Breaking changes (removes field, narrows type)
schema_v3_breaking = {
    "title": "API Response v3",
    "type": "object",
    "properties": {
        "id": {"type": "string"},  # Changed type!
        "name": {"type": "string", "maxLength": 50},  # Reduced limit!
        "status": {"type": "string", "enum": ["active"]},  # Reduced enum!
        # legacy_field removed!
        "email": {"type": "string", "format": "email"},
    },
    "required": ["id", "name", "email"],  # email now required!
}


def check_compatibility(old_schema, new_schema, old_version, new_version):
    """Check and report compatibility between two schemas."""
    print(f"\n{'=' * 60}")
    print(f"Checking: {old_version} → {new_version}")
    print("=" * 60)

    validator = CompatibilityValidator(strict_mode=False)
    result = validator.validate(old_schema, new_schema, old_version, new_version)

    # Display results
    print(f"\nCompatibility Level: {result.level.value.upper()}")
    print(f"Backward Compatible: {'✅' if result.is_backward_compatible else '❌'}")
    print(f"Forward Compatible: {'✅' if result.is_forward_compatible else '❌'}")

    if result.issues:
        print(f"\nIssues Found ({result.issue_count}):")
        for issue in result.issues:
            print(f"  [{issue.severity.upper()}] {issue.path}")
            print(f"    {issue.description}")
            if issue.suggestion:
                print(f"    💡 {issue.suggestion}")

    if result.suggestions:
        print("\nMigration Suggestions:")
        for suggestion in result.suggestions:
            print(f"  • {suggestion}")

    return result.is_backward_compatible


def main():
    """Run compatibility validation examples."""
    print("JSON Schema Compatibility Validator")
    print("====================================\n")
    print("This example demonstrates how to validate schema compatibility")
    print("for safe deployments in production systems.")

    # Test 1: Compatible upgrade (v1 -> v2)
    is_compatible_1 = check_compatibility(
        schema_v1, schema_v2_compatible, "v1.0.0", "v2.0.0"
    )

    # Test 2: Breaking changes (v2 -> v3)
    is_compatible_2 = check_compatibility(
        schema_v2_compatible, schema_v3_breaking, "v2.0.0", "v3.0.0"
    )

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"v1 → v2: {'✅ Safe to deploy' if is_compatible_1 else '❌ Requires migration'}")
    print(f"v2 → v3: {'✅ Safe to deploy' if is_compatible_2 else '❌ Requires migration'}")

    # CI/CD integration example
    print("\n" + "=" * 60)
    print("CI/CD Integration")
    print("=" * 60)
    print("""
To use in CI/CD pipelines, use the CLI:

  # Check compatibility (exits with error code if breaking)
  jsonschema-changelog validate old.json new.json --fail-on-breaking

  # Check without failing (for reporting only)
  jsonschema-changelog validate old.json new.json --no-fail-on-breaking

  # Strict mode (flag more potential issues)
  jsonschema-changelog validate old.json new.json --strict
""")

    # Exit with appropriate code
    if not is_compatible_1 or not is_compatible_2:
        print("\n⚠️  Some schemas have compatibility issues!")
        # In real CI, you might: sys.exit(1)
    else:
        print("\n✅ All schemas are compatible!")


if __name__ == "__main__":
    main()
