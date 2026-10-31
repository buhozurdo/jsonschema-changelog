# jsonschema-changelog

[![CI](https://github.com/buhozurdo/jsonschema-changelog/actions/workflows/ci.yml/badge.svg)](https://github.com/buhozurdo/jsonschema-changelog/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/github/buhozurdo/jsonschema-changelog/graph/badge.svg?token=JYIM9AKYJC)](https://codecov.io/github/buhozurdo/jsonschema-changelog)
[![PyPI version](https://img.shields.io/pypi/v/jsonschema-changelog.svg)](https://pypi.org/project/jsonschema-changelog/)
[![Python versions](https://img.shields.io/pypi/pyversions/jsonschema-changelog.svg)](https://pypi.org/project/jsonschema-changelog/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Detect, document, and manage changes between JSON Schema versions.

Part of the [Búho Zurdo](https://github.com/buhozurdo) ecosystem 🦉

---

## Overview

`jsonschema-changelog` provides deterministic semantic comparison, classification, and changelog generation for JSON Schema specifications.

- **Detect** differences between schema revisions (properties, types, constraints, enums, conditional subschemas `if/then/else`, `dependentRequired`, and dynamic keywords like `unevaluatedProperties`).
- **Classify** changes by operational impact (breaking, non-breaking, deprecations).
- **Generate** human-readable and machine-parseable changelogs (Markdown, JSON, HTML).
- **Validate** backward and forward schema compatibility in CI/CD pipelines.
- **Generate** deterministic data migration scripts.

Designed for data governance in schema-driven architectures, APIs, and clinical/laboratory management systems (LIMS).

---

## Installation

```bash
pip install jsonschema-changelog
```

For development:

```bash
git clone https://github.com/buhozurdo/jsonschema-changelog.git
cd jsonschema-changelog
pip install -e ".[dev]"
```

---

## Quick Start

### Python API

```python
from jsonschema_changelog import SchemaDiff, ChangeClassifier, ChangelogGenerator

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
        "email": {"type": "string", "format": "email"}
    },
    "required": ["name"]
}

# 1. Detect differences
differ = SchemaDiff(old_version="1.0.0", new_version="2.0.0")
diff_result = differ.compare(old_schema, new_schema)

# 2. Classify impact
classifier = ChangeClassifier()
classification = classifier.classify(diff_result)

print(f"Breaking: {len(classification.breaking_changes)}")
print(f"Non-breaking: {len(classification.non_breaking_changes)}")
print(f"Compatible: {classification.is_compatible}")

# 3. Generate changelog
generator = ChangelogGenerator(title="API Schema Changelog")
changelog = generator.generate(classification)
markdown = generator.to_markdown(changelog)
print(markdown)
```

### Command Line Interface

```bash
# Compare schemas
jsonschema-changelog diff old.json new.json

# Generate changelog
jsonschema-changelog changelog old.json new.json --format markdown -o CHANGELOG.md

# Validate compatibility (fails with exit code 1 on breaking changes)
jsonschema-changelog validate old.json new.json --fail-on-breaking

# Generate data migration script
jsonschema-changelog migrate old.json new.json --language python -o migrate.py

# Inspect schema details
jsonschema-changelog info schema.json
```

---

## Change Classification Matrix

| Impact | Description | Examples |
|---|---|---|
| **🚨 Breaking** | Incompatible contract change | Property removed, field made required, enum value removed, constraint narrowed (`minimum` increased). |
| **✨ Non-Breaking** | Backward-compatible addition | Optional property added, required field made optional, enum value added, constraint relaxed. |
| **⚠️ Deprecation** | Marked for future removal | Field annotated with `deprecated: true` or notice in description. |
| **📝 Documentation** | Metadata update | Changes to `title`, `description`, or `examples` without structural impact. |

---

## CI/CD Integration

### GitHub Actions (Fail PR on Breaking Changes)

```yaml
name: Schema Compatibility Check

on:
  pull_request:
    paths:
      - 'schemas/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - run: pip install jsonschema-changelog

      - name: Validate schema compatibility
        run: |
          jsonschema-changelog validate \
            schemas/current.json \
            schemas/proposed.json \
            --fail-on-breaking

      - name: Generate changelog
        if: always()
        run: |
          jsonschema-changelog changelog \
            schemas/current.json \
            schemas/proposed.json \
            --format markdown \
            -o SCHEMA_CHANGELOG.md

      - uses: actions/upload-artifact@v4
        with:
          name: schema-changelog
          path: SCHEMA_CHANGELOG.md
```

### Pre-commit Hook

```yaml
repos:
  - repo: local
    hooks:
      - id: schema-compatibility
        name: Validate Schema Compatibility
        entry: jsonschema-changelog validate
        language: python
        files: \.json$
        args: ['schemas/current.json', 'schemas/proposed.json', '--fail-on-breaking']
```

---

## Alternatives & Competitors

| Solution | Core Approach | Best Use Case | Comparison to `jsonschema-changelog` |
| :--- | :--- | :--- | :--- |
| **`jsonschema-changelog`** | **Semantic Diff & Changelogs** | **Data Governance, CI/CD, Raw Schemas** | **(Baseline)** Lightweight, OpenAPI-agnostic, generates human-readable changelogs/migrations, and robustly handles Draft 2020-12. |
| **`jsonschema-diff`** | Semantic JSON Diff | Simple schema type checks | **Pros:** Minimalist approach to diffing.<br>**Cons:** Lacks changelog/migration generation and robust support for modern dynamic keywords. |
| **`oasdiff`** | OpenAPI Contract Review | HTTP REST APIs | **Pros:** Deeply integrated with OpenAPI semantics (paths, endpoints).<br>**Cons:** Tied to OpenAPI; unsuitable for raw JSON Schemas (e.g. Kafka, NoSQL, LIMS). |
| **Optic** | Managed API Evolution | Enterprise API Platforms | **Pros:** Powerful GUI, history tracking, and platform features.<br>**Cons:** Heavy, commercial vendor lock-in, overkill for agile CI pipelines. |
| **Schema.biz** | Breaking Change Detector | SemVer API Lifecycle | **Pros:** Excellent alignment with Semantic Versioning guarantees.<br>**Cons:** Platform-oriented, less flexible than a fully local open-source Python library. |

---

## Known Limitations

- **Recursive Schemas:** Self-referential `$ref` definitions beyond 10 levels of nesting are truncated to avoid recursion exhaustion.
- **Draft 2020-12 & OpenAPI 3.1 Support:** The library provides broad support for modern JSON Schema keywords (including `unevaluatedProperties`, `unevaluatedItems`, `dependentRequired`, and `if/then/else`). However, highly complex dynamic cross-references or niche schema compositions might still fall back to structural diffs.

---

## Testing

```bash
# Run test suite
pytest

# Run tests with coverage
pytest --cov=src/jsonschema_changelog --cov-report=term-missing
```

---

## Roadmap

Curious about what's next? Check out our [ROADMAP.md](ROADMAP.md) for upcoming features like automated SemVer suggestions, Git history tracking, and interactive UIs.

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and adhere to [Búho Zurdo Engineering Standards](https://github.com/buhozurdo).

1. Fork repository.
2. Create feature branch (`git checkout -b feat/schema-feature`).
3. Add tests and verify formatting.
4. Open Pull Request.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
