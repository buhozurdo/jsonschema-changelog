"""JSONSchema Changelog - Detect, document, and manage JSON Schema changes.

This package provides tools for:
- Detecting differences between JSON Schema versions
- Classifying changes as breaking, non-breaking, or deprecations
- Generating changelogs in multiple formats
- Validating backward/forward compatibility
- Generating migration strategies

Part of the Búho Zurdo ecosystem.
"""

from jsonschema_changelog.changelog import ChangelogGenerator
from jsonschema_changelog.classifier import ChangeCategory, ChangeClassifier
from jsonschema_changelog.compatibility import CompatibilityValidator
from jsonschema_changelog.diff import SchemaDiff
from jsonschema_changelog.migration import MigrationStrategy

__version__ = "0.1.0"
__author__ = "Búho Zurdo"
__email__ = "dev@buhozurdo.com"

__all__ = [
    "SchemaDiff",
    "ChangeClassifier",
    "ChangeCategory",
    "ChangelogGenerator",
    "CompatibilityValidator",
    "MigrationStrategy",
    "__version__",
]
