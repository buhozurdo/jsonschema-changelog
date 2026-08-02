import json
import pytest
import yaml
from pathlib import Path
from jsonschema_changelog.utils import (
    load_schema,
    save_schema,
    extract_version,
    normalize_path,
    get_nested_value,
    set_nested_value,
    deep_merge,
    format_change_summary,
)

class DummyChange:
    def __init__(self, t):
        self.change_type = t

def test_load_schema(tmp_path):
    json_path = tmp_path / "schema.json"
    json_path.write_text('{"type": "object"}')
    assert load_schema(json_path) == {"type": "object"}

    yaml_path = tmp_path / "schema.yaml"
    yaml_path.write_text('type: object')
    assert load_schema(yaml_path) == {"type": "object"}

    txt_path = tmp_path / "schema.txt"
    txt_path.write_text('{"type": "string"}')
    assert load_schema(txt_path) == {"type": "string"}
    
    bad_json = tmp_path / "bad.txt"
    bad_json.write_text('type: invalid')
    assert load_schema(bad_json) == {"type": "invalid"}

    with pytest.raises(FileNotFoundError):
        load_schema(tmp_path / "missing.json")

def test_save_schema(tmp_path):
    schema = {"type": "object"}
    json_path = tmp_path / "schema.json"
    save_schema(schema, json_path)
    assert json.loads(json_path.read_text()) == schema

    yaml_path = tmp_path / "schema.yaml"
    save_schema(schema, yaml_path)
    assert yaml.safe_load(yaml_path.read_text()) == schema

def test_extract_version():
    assert extract_version({"$id": "http://example.com/schema/v1.2.3"}) == "1.2.3"
    assert extract_version({"$id": "http://example.com/schema"}) == "unknown"
    assert extract_version({"version": "2.0.0"}) == "2.0.0"
    assert extract_version({"title": "Schema v3.1.0"}) == "3.1.0"
    assert extract_version({"title": "Schema no version"}) == "unknown"
    assert extract_version({}) == "unknown"

def test_normalize_path():
    assert normalize_path(".properties.foo") == "properties.foo"
    assert normalize_path("foo.properties.bar") == "foo/bar"

def test_get_nested_value():
    data = {"a": {"b": {"c": 1}}}
    assert get_nested_value(data, "a.b.c") == 1
    assert get_nested_value(data, "a.x") is None

def test_set_nested_value():
    data = {"a": {}}
    set_nested_value(data, "a.b.c", 2)
    assert data["a"]["b"]["c"] == 2

def test_deep_merge():
    base = {"a": {"b": 1}, "c": 2}
    overlay = {"a": {"d": 3}, "c": 4}
    merged = deep_merge(base, overlay)
    assert merged == {"a": {"b": 1, "d": 3}, "c": 4}

class UnknownChange:
    pass

def test_format_change_summary():
    assert format_change_summary([]) == "No changes detected"
    changes = [DummyChange("added"), DummyChange("added"), DummyChange("removed"), UnknownChange()]
    assert format_change_summary(changes) == "2 added, 1 removed, 1 unknown"
