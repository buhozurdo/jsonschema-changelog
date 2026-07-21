# jsonschema-changelog

[![Build Status](https://img.shields.io/github/actions/workflow/status/buhozurdo/jsonschema-changelog/python-publish.yml?branch=main)](https://github.com/buhozurdo/jsonschema-changelog/actions)
[![Coverage](https://codecov.io/github/buhozurdo/jsonschema-changelog/graph/badge.svg?token=JYIM9AKYJC)](https://codecov.io/github/buhozurdo/jsonschema-changelog)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Detect, document, and manage changes between JSON Schema versions.**

Part of the [Búho Zurdo](https://github.com/buhozurdo) ecosystem 🦉

---

## 🎯 Overview

`jsonschema-changelog` is a powerful tool for managing JSON Schema evolution in production systems. It helps you:

- **Detect** all changes between schema versions (properties, types, constraints, etc.)
- **Classify** changes as breaking, non-breaking, or deprecations
- **Generate** changelogs in Markdown, JSON, or HTML formats
- **Validate** backward and forward compatibility
- **Create** migration scripts for data transformation

Perfect for APIs, LIMS (Laboratory Information Management Systems), and any system where data schemas evolve over time.

## 📦 Installation

```bash
pip install jsonschema-changelog
```

Or with development dependencies:

```bash
pip install jsonschema-changelog[dev]
```

## 🚀 Quick Start

### Python API

```python
from jsonschema_changelog import SchemaDiff, ChangeClassifier, ChangelogGenerator

# Define your schemas
old_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "status": {"type": "string", "enum": ["active", "inactive"]}
    },
    "required": ["name"]
}

new_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
        "email": {"type": "string", "format": "email"}  # New field
    },
    "required": ["name"]
}

# Detect changes
differ = SchemaDiff(old_version="1.0.0", new_version="2.0.0")
diff_result = differ.compare(old_schema, new_schema)

print(f"Found {diff_result.change_count} changes")

# Classify changes
classifier = ChangeClassifier()
classification = classifier.classify(diff_result)

print(f"Breaking: {len(classification.breaking_changes)}")
print(f"Non-breaking: {len(classification.non_breaking_changes)}")
print(f"Compatible: {classification.is_compatible}")

# Generate changelog
generator = ChangelogGenerator(title="API Schema Changelog")
changelog = generator.generate(classification)
markdown = generator.to_markdown(changelog)
print(markdown)
```

### Command Line

```bash
# Compare two schemas
jsonschema-changelog diff old.json new.json

# Generate changelog
jsonschema-changelog changelog old.json new.json --format markdown -o CHANGELOG.md

# Validate compatibility (fails on breaking changes)
jsonschema-changelog validate old.json new.json --fail-on-breaking

# Generate migration script
jsonschema-changelog migrate old.json new.json --language python -o migrate.py

# Show schema information
jsonschema-changelog info schema.json
```

## 📋 Types of Changes Detected

### Properties
- ➕ Added properties
- ➖ Removed properties
- 🔄 Modified properties (type, constraints, etc.)

### Required Fields
- 🔒 Fields becoming required
- 🔓 Fields becoming optional

### Types
- 📝 Type changes (string → integer, etc.)
- 📋 Type unions (adding/removing types)

### Constraints
- 📏 Length constraints (minLength, maxLength)
- 🔢 Numeric constraints (minimum, maximum)
- 📊 Array constraints (minItems, maxItems)

### Enums
- ✅ Added enum values
- ❌ Removed enum values

### Other
- 📄 Format changes (email, date-time, etc.)
- 🔤 Pattern changes (regex)
- 📚 $ref changes
- ⚠️ Deprecations
- 📝 Documentation changes

## 🏷️ Change Classification

Changes are automatically classified by their impact:

### 🚨 Breaking Changes
- Removing a property
- Making a field required
- Reducing enum values
- Making constraints stricter (higher minLength, lower maximum)
- Changing type to a narrower type

### ✨ Non-Breaking Changes
- Adding optional properties
- Making a field optional
- Adding enum values
- Relaxing constraints
- Adding nullable to types

### ⚠️ Deprecations
- Marking fields as deprecated
- Adding deprecation notices in descriptions

### 📝 Documentation Changes
- Title/description updates
- Example changes

## 🔧 API Reference

### SchemaDiff

```python
from jsonschema_changelog import SchemaDiff

differ = SchemaDiff(
    old_version="1.0.0",
    new_version="2.0.0",
    include_documentation=True  # Include title/description changes
)

result = differ.compare(old_schema, new_schema)

# Access changes
for change in result.changes:
    print(f"{change.change_type}: {change.path}")
    print(f"  {change.description}")
```

### ChangeClassifier

```python
from jsonschema_changelog import ChangeClassifier

classifier = ChangeClassifier(strict_mode=False)
classification = classifier.classify(diff_result)

# Access classified changes
for change in classification.breaking_changes:
    print(f"🚨 {change.impact_description}")
    print(f"   Migration: {change.migration_hint}")
```

### ChangelogGenerator

```python
from jsonschema_changelog import ChangelogGenerator

generator = ChangelogGenerator(
    title="My API Changelog",
    description="Track schema changes",
    include_documentation=False
)

changelog = generator.generate(classification, date="2024-01-15")

# Multiple formats
markdown = generator.to_markdown(changelog)
json_output = generator.to_json(changelog)
html = generator.to_html(changelog)
```

### CompatibilityValidator

```python
from jsonschema_changelog import CompatibilityValidator

validator = CompatibilityValidator(strict_mode=False)
result = validator.validate(old_schema, new_schema)

print(f"Level: {result.level}")  # FULL, BACKWARD, FORWARD, or NONE
print(f"Backward compatible: {result.is_backward_compatible}")
print(f"Forward compatible: {result.is_forward_compatible}")

for issue in result.issues:
    print(f"Issue: {issue.description}")
    print(f"Suggestion: {issue.suggestion}")
```

### MigrationStrategy

```python
from jsonschema_changelog.migration import MigrationStrategy

strategy = MigrationStrategy()
plan = strategy.generate(classification)

# Generate migration scripts
python_script = plan.to_script("python")
js_script = plan.to_script("javascript")

# Execute migration on data
migrated_data = strategy.execute(plan, original_data)
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Schema Validation

on:
  pull_request:
    paths:
      - 'schemas/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - run: pip install jsonschema-changelog

      - name: Validate schema compatibility
        run: |
          jsonschema-changelog validate \
            schemas/schema_v1.json \
            schemas/schema_v2.json \
            --fail-on-breaking

      - name: Generate changelog
        if: always()
        run: |
          jsonschema-changelog changelog \
            schemas/schema_v1.json \
            schemas/schema_v2.json \
            --format markdown \
            --output SCHEMA_CHANGELOG.md

      - name: Upload changelog
        uses: actions/upload-artifact@v4
        with:
          name: schema-changelog
          path: SCHEMA_CHANGELOG.md
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: schema-compatibility
        name: Check Schema Compatibility
        entry: jsonschema-changelog validate
        language: python
        files: \.json$
        args: ['schemas/current.json', 'schemas/proposed.json']
```

## 🏥 LIMS Use Case

This tool was designed with Laboratory Information Management Systems in mind:

```python
# Validate that patient data schema changes don't break existing records
from jsonschema_changelog import CompatibilityValidator

validator = CompatibilityValidator()
result = validator.validate(
    old_schema=patient_schema_v1,
    new_schema=patient_schema_v2,
    old_version="1.0.0",
    new_version="2.0.0"
)

if not result.is_backward_compatible:
    print("⚠️ Breaking changes detected!")
    print("Existing patient records may be affected.")
    
    for suggestion in result.suggestions:
        print(f"• {suggestion}")
```

## 🛣️ Roadmap

- [ ] JSON Schema Draft 2020-12 full support
- [ ] Schema versioning with Git integration
- [ ] Visual diff in HTML output
- [ ] Migration validation with sample data
- [ ] OpenAPI/Swagger schema support
- [ ] AsyncAPI schema support
- [ ] Database schema comparison

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <img src="https://img.freepik.com/premium-vector/letter-b-owl-mascot-esport-gaming-logo-design-owl-night-bird-illustration-bird-gamer-esport-logo_15602-2190.jpg" alt="Búho Zurdo" width="100">
  <br>
  Part of the <strong>Búho Zurdo</strong> ecosystem
  <br>
  <em>Building reliable software, one schema at a time</em>
</p>
