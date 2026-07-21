"""Command-line interface for jsonschema-changelog.

Provides commands for comparing schemas, generating changelogs,
validating compatibility, and generating migration scripts.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from jsonschema_changelog import __version__
from jsonschema_changelog.changelog import ChangelogGenerator
from jsonschema_changelog.classifier import ChangeClassifier
from jsonschema_changelog.compatibility import (
    CompatibilityResult,
    CompatibilityValidator,
)
from jsonschema_changelog.diff import DiffResult, SchemaDiff
from jsonschema_changelog.migration import MigrationStrategy
from jsonschema_changelog.utils import extract_version, load_schema


@click.group()
@click.version_option(version=__version__, prog_name="jsonschema-changelog")
def main() -> None:
    """JSONSchema Changelog - Detect, document, and manage JSON Schema changes.

    Part of the Búho Zurdo ecosystem.
    """
    pass


@main.command()
@click.argument("old_schema", type=click.Path(exists=True))
@click.argument("new_schema", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format",
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file (stdout if not specified)"
)
@click.option("--old-version", help="Version label for old schema")
@click.option("--new-version", help="Version label for new schema")
@click.option(
    "--include-docs/--no-include-docs",
    default=True,
    help="Include documentation changes",
)
def diff(
    old_schema: str,
    new_schema: str,
    output_format: str,
    output: Optional[str],
    old_version: Optional[str],
    new_version: Optional[str],
    include_docs: bool,
) -> None:
    """Compare two JSON schemas and show differences.

    OLD_SCHEMA: Path to the original schema file
    NEW_SCHEMA: Path to the modified schema file

    Example:
        jsonschema-changelog diff schema_v1.json schema_v2.json

    """
    try:
        old = load_schema(old_schema)
        new = load_schema(new_schema)

        # Extract versions if not provided
        if not old_version:
            old_version = extract_version(old) or Path(old_schema).stem
        if not new_version:
            new_version = extract_version(new) or Path(new_schema).stem

        differ = SchemaDiff(
            old_version=old_version,
            new_version=new_version,
            include_documentation=include_docs,
        )
        result = differ.compare(old, new)

        if output_format == "json":
            import json

            content = json.dumps(result.to_dict(), indent=2)
        elif output_format == "markdown":
            content = _format_diff_markdown(result)
        else:
            content = _format_diff_text(result)

        _write_output(content, output)

        # Exit with non-zero if changes found
        if result.has_changes:
            click.echo(f"\n{result.change_count} change(s) detected", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("old_schema", type=click.Path(exists=True))
@click.argument("new_schema", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["markdown", "json", "html"]),
    default="markdown",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.option("--title", default="Schema Changelog", help="Changelog title")
@click.option("--date", help="Date for the changelog entry (YYYY-MM-DD)")
@click.option("--old-version", help="Version label for old schema")
@click.option("--new-version", help="Version label for new schema")
def changelog(
    old_schema: str,
    new_schema: str,
    output_format: str,
    output: Optional[str],
    title: str,
    date: Optional[str],
    old_version: Optional[str],
    new_version: Optional[str],
) -> None:
    """Generate a changelog between two schema versions.

    OLD_SCHEMA: Path to the original schema file
    NEW_SCHEMA: Path to the modified schema file

    Example:
        jsonschema-changelog changelog v1/schema.json v2/schema.json -f markdown -o CHANGELOG.md

    """
    try:
        old = load_schema(old_schema)
        new = load_schema(new_schema)

        # Extract versions if not provided
        if not old_version:
            old_version = extract_version(old) or Path(old_schema).stem
        if not new_version:
            new_version = extract_version(new) or Path(new_schema).stem

        # Generate diff and classify
        differ = SchemaDiff(old_version=old_version, new_version=new_version)
        diff_result = differ.compare(old, new)

        classifier = ChangeClassifier()
        classification = classifier.classify(diff_result)

        # Generate changelog
        generator = ChangelogGenerator(title=title)
        changelog_obj = generator.generate(classification, date=date)

        # Format output
        content = generator.format(changelog_obj, output_format)

        _write_output(content, output)

        # Summary
        summary = classification.summary
        click.echo(
            f"Generated changelog: {summary['breaking']} breaking, "
            f"{summary['non_breaking']} non-breaking, "
            f"{summary['deprecation']} deprecations",
            err=True,
        )

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("old_schema", type=click.Path(exists=True))
@click.argument("new_schema", type=click.Path(exists=True))
@click.option(
    "--strict/--no-strict", default=False, help="Strict compatibility checking"
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.option(
    "--fail-on-breaking/--no-fail-on-breaking",
    default=True,
    help="Exit with error code if breaking changes found",
)
def validate(
    old_schema: str,
    new_schema: str,
    strict: bool,
    output_format: str,
    output: Optional[str],
    fail_on_breaking: bool,
) -> None:
    """Validate compatibility between schema versions.

    Checks backward and forward compatibility between schemas.

    OLD_SCHEMA: Path to the original schema file
    NEW_SCHEMA: Path to the modified schema file

    Example:
        jsonschema-changelog validate old.json new.json --strict

    """
    try:
        old = load_schema(old_schema)
        new = load_schema(new_schema)

        validator = CompatibilityValidator(strict_mode=strict)
        result = validator.validate(old, new)

        if output_format == "json":
            import json

            content = json.dumps(result.to_dict(), indent=2)
        else:
            content = _format_compatibility_text(result)

        _write_output(content, output)

        # Exit code based on compatibility
        if fail_on_breaking and not result.is_backward_compatible:
            click.echo("\n❌ Backward compatibility broken", err=True)
            sys.exit(1)
        elif result.is_fully_compatible:
            click.echo("\n✅ Schemas are fully compatible", err=True)
        elif result.is_backward_compatible:
            click.echo("\n⚠️ Backward compatible, but not forward compatible", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("old_schema", type=click.Path(exists=True))
@click.argument("new_schema", type=click.Path(exists=True))
@click.option(
    "--language",
    "-l",
    type=click.Choice(["python", "javascript"]),
    default="python",
    help="Script language",
)
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.option("--old-version", help="Version label for old schema")
@click.option("--new-version", help="Version label for new schema")
def migrate(
    old_schema: str,
    new_schema: str,
    language: str,
    output: Optional[str],
    old_version: Optional[str],
    new_version: Optional[str],
) -> None:
    """Generate a migration script between schema versions.

    Creates a script that can transform data from old schema to new schema.

    OLD_SCHEMA: Path to the original schema file
    NEW_SCHEMA: Path to the modified schema file

    Example:
        jsonschema-changelog migrate v1.json v2.json -l python -o migrate.py

    """
    try:
        old = load_schema(old_schema)
        new = load_schema(new_schema)

        # Extract versions if not provided
        if not old_version:
            old_version = extract_version(old) or Path(old_schema).stem
        if not new_version:
            new_version = extract_version(new) or Path(new_schema).stem

        # Generate diff and classify
        differ = SchemaDiff(old_version=old_version, new_version=new_version)
        diff_result = differ.compare(old, new)

        classifier = ChangeClassifier()
        classification = classifier.classify(diff_result)

        # Generate migration plan
        strategy = MigrationStrategy()
        plan = strategy.generate(classification)

        # Generate script
        content = plan.to_script(language)

        _write_output(content, output)

        # Summary
        click.echo(
            f"Generated migration script: {plan.step_count} steps, "
            f"reversible: {plan.is_reversible}",
            err=True,
        )

        if plan.warnings:
            click.echo("\nWarnings:", err=True)
            for warning in plan.warnings:
                click.echo(f"  ⚠️ {warning}", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("schema", type=click.Path(exists=True))
def info(schema: str) -> None:
    """Show information about a schema.

    SCHEMA: Path to the schema file

    Example:
        jsonschema-changelog info schema.json

    """
    try:
        data = load_schema(schema)

        click.echo(f"📄 Schema: {schema}")
        click.echo(f"   Version: {extract_version(data)}")
        click.echo(f"   $id: {data.get('$id', 'N/A')}")
        click.echo(f"   Title: {data.get('title', 'N/A')}")
        click.echo(f"   $schema: {data.get('$schema', 'N/A')}")

        if "properties" in data:
            props = data["properties"]
            required = set(data.get("required", []))
            click.echo(f"   Properties: {len(props)}")
            for name in sorted(props.keys()):
                req_marker = "*" if name in required else " "
                prop_type = props[name].get("type", "any")
                click.echo(f"      {req_marker} {name}: {prop_type}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _write_output(content: str, output: Optional[str]) -> None:
    """Write content to file or stdout."""
    if output:
        Path(output).write_text(content, encoding="utf-8")
        click.echo(f"Output written to: {output}", err=True)
    else:
        click.echo(content)


def _format_diff_text(result: DiffResult) -> str:
    """Format diff result as text."""
    lines = [
        f"Schema Diff: {result.old_version} → {result.new_version}",
        f"Changes: {result.change_count}",
        "=" * 50,
    ]

    for change in result.changes:
        lines.append(f"\n[{change.change_type.value.upper()}] {change.path}")
        lines.append(f"  {change.description}")
        if change.old_value is not None:
            lines.append(f"  Old: {change.old_value}")
        if change.new_value is not None:
            lines.append(f"  New: {change.new_value}")

    return "\n".join(lines)


def _format_diff_markdown(result: DiffResult) -> str:
    """Format diff result as Markdown."""
    lines = [
        f"# Schema Diff: {result.old_version} → {result.new_version}",
        "",
        f"**Changes:** {result.change_count}",
        "",
    ]

    for change in result.changes:
        lines.append(f"## {change.change_type.value.upper()}: `{change.path}`")
        lines.append(f"{change.description}")
        if change.old_value is not None:
            lines.append(f"- **Old:** `{change.old_value}`")
        if change.new_value is not None:
            lines.append(f"- **New:** `{change.new_value}`")
        lines.append("")

    return "\n".join(lines)


def _format_compatibility_text(result: CompatibilityResult) -> str:
    """Format compatibility result as text."""
    lines = [
        f"Compatibility Check: {result.old_version} → {result.new_version}",
        "=" * 50,
        f"Level: {result.level.value.upper()}",
        f"Backward Compatible: {'✅' if result.is_backward_compatible else '❌'}",
        f"Forward Compatible: {'✅' if result.is_forward_compatible else '❌'}",
    ]

    if result.issues:
        lines.append(f"\nIssues ({result.issue_count}):")
        for issue in result.issues:
            lines.append(f"  [{issue.severity.upper()}] {issue.path}")
            lines.append(f"    {issue.description}")
            if issue.suggestion:
                lines.append(f"    💡 {issue.suggestion}")

    if result.suggestions:
        lines.append("\nSuggestions:")
        for suggestion in result.suggestions:
            lines.append(f"  • {suggestion}")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
