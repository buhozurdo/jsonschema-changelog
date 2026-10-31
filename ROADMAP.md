# jsonschema-changelog Roadmap

This document outlines the planned features and strategic direction for upcoming versions of `jsonschema-changelog`.

## [0.3.0] - Developer Experience & CI/CD
*Focus on bringing the tool closer to the developer workflow and making CI/CD integrations seamless.*

- **Automated SemVer Bump Recommendations**: 
  - Introduce a new command (`suggest-bump`) to intelligently recommend Semantic Versioning increments (Major, Minor, Patch) based on the strict classification of detected changes.
- **Native CI/CD Annotations (GitHub Actions)**: 
  - Add specialized output formatting (`--format github-actions`) that emits native workflow commands. This will allow CI bots to annotate Pull Requests directly on the offending lines when a breaking change is detected.

## [0.4.0] - Deep Insights & Visualization
*Focus on understanding schema evolution over time and improving visual developer tooling.*

- **Git History Explorer**: 
  - A command (e.g., `git-history`) that traverses a repository's commit history for a target schema file, generating a comprehensive, sequential timeline of all structural changes since its inception.
- **Interactive Local UI Preview**: 
  - A lightweight, zero-dependency local web server (`serve` command) to interactively preview schema diffs in the browser, eliminating the need to manually export and open static HTML files.

## [1.0.0] - Enterprise Stability & Performance
*Focus on enterprise readiness, ensuring the library is robust enough for massive-scale architectures.*

- **Performance Optimization**: 
  - Memory and speed optimizations for comparing massive, heavily-nested schemas (thousands of lines).
- **API Stabilization**: 
  - Absolute stabilization of the public Python API with strict backward compatibility guarantees.
- **Ecosystem Extensibility**: 
  - Enhanced support for generating migration scripts in multiple languages (SQL, TypeScript, JQ).
