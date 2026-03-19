#!/usr/bin/env python3
"""Example: Generate a changelog from schema changes.

This example shows how to generate changelogs in different formats
(Markdown, JSON, HTML) from schema version comparisons.
"""

from jsonschema_changelog import (
    ChangeClassifier,
    ChangelogGenerator,
    SchemaDiff,
)

# Sample schemas representing LIMS evolution
schema_v1 = {
    "title": "Sample Schema v1",
    "type": "object",
    "properties": {
        "sample_id": {"type": "string"},
        "type": {"type": "string", "enum": ["blood", "urine"]},
        "status": {"type": "string"},
    },
    "required": ["sample_id", "type"],
}

schema_v2 = {
    "title": "Sample Schema v2",
    "type": "object",
    "properties": {
        "sample_id": {"type": "string"},
        "type": {"type": "string", "enum": ["blood", "urine", "tissue", "swab"]},
        "status": {"type": "string", "enum": ["pending", "processing", "completed"]},
        "priority": {"type": "string", "enum": ["routine", "urgent", "stat"]},
        "collected_at": {"type": "string", "format": "date-time"},
    },
    "required": ["sample_id", "type"],
}


def main():
    """Generate changelog in multiple formats."""
    print("=" * 60)
    print("Changelog Generation Example")
    print("=" * 60)
    print()

    # Step 1: Detect differences
    differ = SchemaDiff(old_version="1.0.0", new_version="2.0.0")
    diff_result = differ.compare(schema_v1, schema_v2)

    print(f"Detected {diff_result.change_count} changes")
    print()

    # Step 2: Classify changes
    classifier = ChangeClassifier()
    classification = classifier.classify(diff_result)

    print("Classification summary:")
    print(f"  Breaking changes: {len(classification.breaking_changes)}")
    print(f"  Non-breaking changes: {len(classification.non_breaking_changes)}")
    print(f"  Deprecations: {len(classification.deprecations)}")
    print(f"  Backward compatible: {classification.is_compatible}")
    print()

    # Step 3: Generate changelog
    generator = ChangelogGenerator(
        title="LIMS Sample Schema Changelog",
        description="Track changes to the laboratory sample data schema",
        include_documentation=False,
    )
    changelog = generator.generate(classification, date="2024-01-15")

    # Generate Markdown format
    print("=" * 40)
    print("MARKDOWN FORMAT")
    print("=" * 40)
    markdown = generator.to_markdown(changelog)
    print(markdown)

    # Generate JSON format
    print("\n" + "=" * 40)
    print("JSON FORMAT (abbreviated)")
    print("=" * 40)
    json_output = generator.to_json(changelog)
    # Print first 500 chars for brevity
    print(json_output[:500] + "...")

    # Generate HTML format
    print("\n" + "=" * 40)
    print("HTML FORMAT (abbreviated)")
    print("=" * 40)
    html_output = generator.to_html(changelog)
    # Print first 500 chars for brevity
    print(html_output[:500] + "...")

    # Save to files
    print("\n" + "=" * 40)
    print("Saving changelog files...")
    print("=" * 40)

    with open("CHANGELOG.md", "w") as f:
        f.write(markdown)
    print("✓ Saved CHANGELOG.md")

    with open("changelog.json", "w") as f:
        f.write(json_output)
    print("✓ Saved changelog.json")

    with open("changelog.html", "w") as f:
        f.write(html_output)
    print("✓ Saved changelog.html")


if __name__ == "__main__":
    main()
