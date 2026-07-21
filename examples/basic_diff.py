#!/usr/bin/env python3
"""Basic example: Compare two JSON schemas and show differences.

This example demonstrates how to use the SchemaDiff class to detect
changes between two schema versions.
"""

from jsonschema_changelog import SchemaDiff

# Define two schema versions
schema_v1 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Patient Record v1",
    "type": "object",
    "properties": {
        "patient_id": {
            "type": "string",
            "description": "Unique patient identifier",
        },
        "name": {
            "type": "string",
            "maxLength": 100,
        },
        "date_of_birth": {
            "type": "string",
            "format": "date",
        },
        "status": {
            "type": "string",
            "enum": ["active", "inactive"],
        },
    },
    "required": ["patient_id", "name"],
}

schema_v2 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Patient Record v2",
    "type": "object",
    "properties": {
        "patient_id": {
            "type": "string",
            "description": "Unique patient identifier",
            "pattern": "^PAT-[0-9]{8}$",  # Added pattern validation
        },
        "name": {
            "type": "string",
            "maxLength": 200,  # Increased max length
        },
        "date_of_birth": {
            "type": "string",
            "format": "date",
        },
        "status": {
            "type": "string",
            "enum": ["active", "inactive", "deceased", "transferred"],  # Added values
        },
        "email": {  # New optional field
            "type": "string",
            "format": "email",
        },
        "phone": {  # New optional field
            "type": "string",
        },
    },
    "required": ["patient_id", "name"],
}


def main():
    """Run the basic diff example."""
    print("=" * 60)
    print("JSON Schema Diff Example")
    print("=" * 60)
    print()

    # Create differ with version labels
    differ = SchemaDiff(
        old_version="1.0.0",
        new_version="2.0.0",
        include_documentation=True,
    )

    # Compare schemas
    result = differ.compare(schema_v1, schema_v2)

    # Display results
    print(f"Comparing: {result.old_version} → {result.new_version}")
    print(f"Total changes: {result.change_count}")
    print()

    if not result.has_changes:
        print("No changes detected.")
        return

    # Group and display changes by type
    for change in result.changes:
        print(f"[{change.change_type.value.upper()}] {change.path}")
        print(f"  {change.description}")
        if change.old_value is not None:
            print(f"  Old: {change.old_value}")
        if change.new_value is not None:
            print(f"  New: {change.new_value}")
        print()

    # Export as dictionary (for JSON serialization)
    print("\nJSON representation:")
    import json

    print(json.dumps(result.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()
