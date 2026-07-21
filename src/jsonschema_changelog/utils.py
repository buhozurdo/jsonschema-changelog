"""Utility functions for jsonschema-changelog."""

import json
from pathlib import Path
from typing import Any, Dict, Union

import yaml


def load_schema(path: Union[str, Path]) -> Dict[str, Any]:
    """Load a JSON Schema from a file.

    Supports both JSON and YAML formats.

    Args:
        path: Path to the schema file

    Returns:
        Loaded schema as dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is not supported

    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    content = path.read_text(encoding="utf-8")

    if path.suffix.lower() in (".json",):
        return json.loads(content)
    elif path.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(content)
    else:
        # Try JSON first, then YAML
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return yaml.safe_load(content)


def save_schema(schema: Dict[str, Any], path: Union[str, Path]) -> None:
    """Save a JSON Schema to a file.

    Args:
        schema: The schema to save
        path: Path to save the schema to

    """
    path = Path(path)

    if path.suffix.lower() in (".yaml", ".yml"):
        content = yaml.dump(schema, default_flow_style=False, sort_keys=False)
    else:
        content = json.dumps(schema, indent=2)

    path.write_text(content, encoding="utf-8")


def extract_version(schema: Dict[str, Any]) -> str:
    """Extract version from a schema.

    Looks for version in common locations:
    - $id (e.g., "https://example.com/schema/v1.0.0")
    - version property
    - title (e.g., "My Schema v1.0.0")

    Args:
        schema: The schema to extract version from

    Returns:
        Extracted version string or "unknown"

    """
    # Check $id for version
    schema_id = schema.get("$id", "")
    if schema_id:
        # Look for version pattern in ID
        import re

        version_match = re.search(r"v?(\d+\.\d+\.\d+)", schema_id)
        if version_match:
            return version_match.group(1)

    # Check version property
    if "version" in schema:
        return str(schema["version"])

    # Check title
    title = schema.get("title", "")
    if title:
        import re

        version_match = re.search(r"v?(\d+\.\d+\.\d+)", title)
        if version_match:
            return version_match.group(1)

    return "unknown"


def normalize_path(path: str) -> str:
    """Normalize a JSON path.

    Args:
        path: The path to normalize

    Returns:
        Normalized path

    """
    # Remove leading dots
    path = path.lstrip(".")

    # Normalize property accessors
    path = path.replace(".properties.", "/")

    return path


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Get a nested value from a dictionary.

    Args:
        data: The dictionary to get value from
        path: Dot-separated path to the value

    Returns:
        The value at the path, or None if not found

    """
    parts = path.split(".")
    current = data

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
    """Set a nested value in a dictionary.

    Args:
        data: The dictionary to set value in
        path: Dot-separated path to the value
        value: The value to set

    """
    parts = path.split(".")
    current = data

    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value


def deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: The base dictionary
        overlay: The dictionary to merge on top

    Returns:
        Merged dictionary

    """
    result = base.copy()

    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def format_change_summary(changes: list) -> str:
    """Format a summary of changes.

    Args:
        changes: List of changes

    Returns:
        Formatted summary string

    """
    if not changes:
        return "No changes detected"

    # Count by type
    type_counts: Dict[str, int] = {}
    for change in changes:
        change_type = getattr(change, "change_type", "unknown")
        if hasattr(change_type, "value"):
            change_type = change_type.value
        type_counts[str(change_type)] = type_counts.get(str(change_type), 0) + 1

    parts = [f"{count} {ctype}" for ctype, count in sorted(type_counts.items())]
    return ", ".join(parts)
