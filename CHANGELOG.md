# Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.1] - 2026-11-05

### Security & CI
- Pinned GitHub Actions dependencies to full commit SHAs in all workflows.
- Added SonarQube / SonarCloud scanning workflow and updated `sonar-project.properties`.
- Pinned `pip install --only-binary :all:` in release workflows.
- Fixed bash test syntax (`[[ ... ]]`) and error redirection in `examples/ci_integration.sh`.

### Changed & Refactored
- Decomposed complex functions in `classifier.py`, `diff.py`, and `migration.py` to reduce cognitive complexity.
- Replaced backtracking regular expression in `utils.py` with safe semver parsing to eliminate ReDoS risk.
- Modernized union type annotations (`|`) in `utils.py`.
- Optimized list extensions and set comprehensions across formatters and diff modules.

---

## [0.2.0] - 2026-10-07

### Added
- Implementation of full evaluation for dynamic keywords (`unevaluatedProperties` and `unevaluatedItems`).
- Improvement of the inference engine for complex conditions (`dependentRequired` and `if/then/else`).

---

## [0.1.5] - 2026-08-01
- Added PyPI release.yml

---

## [0.1.0] - 2026-07-21

### Added