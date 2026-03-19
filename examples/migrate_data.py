#!/usr/bin/env python3
"""Example: Generate and execute data migration scripts.

This example shows how to create migration strategies and scripts
for transforming data between schema versions.
"""

import json

from jsonschema_changelog import ChangeClassifier, SchemaDiff
from jsonschema_changelog.migration import MigrationStrategy

# Schema versions
schema_v1 = {
    "title": "Patient v1",
    "type": "object",
    "properties": {
        "patient_id": {"type": "string"},
        "full_name": {"type": "string"},
        "age": {"type": "string"},  # Stored as string
        "status": {"type": "string"},
    },
    "required": ["patient_id", "full_name"],
}

schema_v2 = {
    "title": "Patient v2",
    "type": "object",
    "properties": {
        "patient_id": {"type": "string"},
        "full_name": {"type": "string"},
        "age": {"type": "integer"},  # Now integer
        "status": {"type": "string", "default": "active"},
        "email": {"type": "string"},  # New field
        "created_at": {"type": "string", "format": "date-time"},  # New field
    },
    "required": ["patient_id", "full_name", "status"],  # status now required
}

# Sample data in v1 format
sample_data_v1 = [
    {
        "patient_id": "PAT-001",
        "full_name": "John Doe",
        "age": "35",
        "status": "active",
    },
    {
        "patient_id": "PAT-002",
        "full_name": "Jane Smith",
        "age": "28",
        # Missing status
    },
    {
        "patient_id": "PAT-003",
        "full_name": "Bob Johnson",
        # Missing age and status
    },
]


def main():
    """Demonstrate migration strategy generation and execution."""
    print("=" * 60)
    print("Data Migration Example")
    print("=" * 60)
    print()

    # Step 1: Analyze schema changes
    print("Step 1: Analyzing schema changes...")
    differ = SchemaDiff(old_version="1.0.0", new_version="2.0.0")
    diff_result = differ.compare(schema_v1, schema_v2)

    print(f"  Detected {diff_result.change_count} changes")
    print()

    # Step 2: Classify changes
    print("Step 2: Classifying changes...")
    classifier = ChangeClassifier()
    classification = classifier.classify(diff_result)

    print(f"  Breaking changes: {len(classification.breaking_changes)}")
    print(f"  Non-breaking changes: {len(classification.non_breaking_changes)}")
    print()

    # Step 3: Generate migration plan
    print("Step 3: Generating migration plan...")
    strategy = MigrationStrategy()
    plan = strategy.generate(classification)

    print(f"  Migration steps: {plan.step_count}")
    print(f"  Reversible: {plan.is_reversible}")
    print()

    if plan.warnings:
        print("  ⚠️ Warnings:")
        for warning in plan.warnings:
            print(f"    - {warning}")
        print()

    # Display migration steps
    print("  Migration steps:")
    for i, step in enumerate(plan.steps, 1):
        print(f"    {i}. [{step.operation.value}] {step.description}")
    print()

    # Step 4: Generate Python migration script
    print("Step 4: Generating Python migration script...")
    python_script = plan.to_script("python")
    
    print("\n--- migrate.py ---")
    print(python_script[:1000])  # Show first 1000 chars
    if len(python_script) > 1000:
        print("... (truncated)")
    print("--- end ---\n")

    # Save the script
    with open("migrate.py", "w") as f:
        f.write(python_script)
    print("✓ Saved migrate.py")

    # Step 5: Generate JavaScript migration script
    print("\nStep 5: Generating JavaScript migration script...")
    js_script = plan.to_script("javascript")
    
    with open("migrate.js", "w") as f:
        f.write(js_script)
    print("✓ Saved migrate.js")

    # Step 6: Execute migration on sample data
    print("\nStep 6: Executing migration on sample data...")
    print("\nOriginal data (v1):")
    print(json.dumps(sample_data_v1, indent=2))

    migrated_data = []
    for record in sample_data_v1:
        migrated = strategy.execute(plan, record)
        migrated_data.append(migrated)

    print("\nMigrated data (v2):")
    print(json.dumps(migrated_data, indent=2))

    # Step 7: Validate migrated data
    print("\nStep 7: Validating migrated data against v2 schema...")
    from jsonschema import validate, ValidationError

    all_valid = True
    for i, record in enumerate(migrated_data):
        try:
            validate(instance=record, schema=schema_v2)
            print(f"  Record {i + 1}: ✅ Valid")
        except ValidationError as e:
            print(f"  Record {i + 1}: ❌ Invalid - {e.message}")
            all_valid = False

    if all_valid:
        print("\n✅ All records migrated successfully!")
    else:
        print("\n⚠️ Some records need manual review")


if __name__ == "__main__":
    main()
