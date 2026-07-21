"""Tests for the CLI module."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from jsonschema_changelog.cli import main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def schema_v1_path():
    return str(FIXTURES_DIR / "schema_v1.json")


@pytest.fixture
def schema_v2_path():
    return str(FIXTURES_DIR / "schema_v2.json")


@pytest.fixture
def schema_v3_path():
    return str(FIXTURES_DIR / "schema_v3_breaking.json")


class TestDiffCommand:
    """Tests for diff command."""

    def test_diff_basic(self, runner, schema_v1_path, schema_v2_path):
        """Test basic diff command."""
        result = runner.invoke(main, ["diff", schema_v1_path, schema_v2_path])

        assert result.exit_code == 0
        assert "change" in result.output.lower()

    def test_diff_json_format(self, runner, schema_v1_path, schema_v2_path):
        """Test diff with JSON format."""
        result = runner.invoke(
            main, ["diff", schema_v1_path, schema_v2_path, "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "changes" in data

    def test_diff_markdown_format(self, runner, schema_v1_path, schema_v2_path):
        """Test diff with Markdown format."""
        result = runner.invoke(
            main, ["diff", schema_v1_path, schema_v2_path, "--format", "markdown"]
        )

        assert result.exit_code == 0
        assert "#" in result.output

    def test_diff_with_versions(self, runner, schema_v1_path, schema_v2_path):
        """Test diff with custom versions."""
        result = runner.invoke(
            main,
            [
                "diff",
                schema_v1_path,
                schema_v2_path,
                "--old-version",
                "1.0.0",
                "--new-version",
                "2.0.0",
            ],
        )

        assert result.exit_code == 0
        assert "1.0.0" in result.output or "2.0.0" in result.output

    def test_diff_nonexistent_file(self, runner, schema_v1_path):
        """Test diff with nonexistent file."""
        result = runner.invoke(main, ["diff", schema_v1_path, "nonexistent.json"])

        assert result.exit_code != 0


class TestChangelogCommand:
    """Tests for changelog command."""

    def test_changelog_basic(self, runner, schema_v1_path, schema_v2_path):
        """Test basic changelog command."""
        result = runner.invoke(main, ["changelog", schema_v1_path, schema_v2_path])

        assert result.exit_code == 0
        assert "#" in result.output  # Markdown header

    def test_changelog_json_format(self, runner, schema_v1_path, schema_v2_path):
        """Test changelog with JSON format."""
        result = runner.invoke(
            main, ["changelog", schema_v1_path, schema_v2_path, "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "entries" in data

    def test_changelog_html_format(self, runner, schema_v1_path, schema_v2_path):
        """Test changelog with HTML format."""
        result = runner.invoke(
            main, ["changelog", schema_v1_path, schema_v2_path, "--format", "html"]
        )

        assert result.exit_code == 0
        assert "<html" in result.output

    def test_changelog_with_title(self, runner, schema_v1_path, schema_v2_path):
        """Test changelog with custom title."""
        result = runner.invoke(
            main,
            [
                "changelog",
                schema_v1_path,
                schema_v2_path,
                "--title",
                "My Custom Changelog",
            ],
        )

        assert result.exit_code == 0
        assert "My Custom Changelog" in result.output

    def test_changelog_with_output_file(
        self, runner, schema_v1_path, schema_v2_path, tmp_path
    ):
        """Test changelog output to file."""
        output_file = tmp_path / "CHANGELOG.md"
        result = runner.invoke(
            main,
            [
                "changelog",
                schema_v1_path,
                schema_v2_path,
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "#" in content


class TestValidateCommand:
    """Tests for validate command."""

    def test_validate_compatible(self, runner, schema_v1_path, schema_v2_path):
        """Test validate with compatible schemas."""
        result = runner.invoke(main, ["validate", schema_v1_path, schema_v2_path])

        # v1 to v2 is backward compatible
        assert result.exit_code == 0
        assert "compatible" in result.output.lower()

    def test_validate_incompatible(self, runner, schema_v2_path, schema_v3_path):
        """Test validate with incompatible schemas."""
        result = runner.invoke(main, ["validate", schema_v2_path, schema_v3_path])

        # v2 to v3 has breaking changes
        assert result.exit_code != 0
        assert "broken" in result.output.lower() or "❌" in result.output

    def test_validate_no_fail_on_breaking(self, runner, schema_v2_path, schema_v3_path):
        """Test validate without failing on breaking changes."""
        result = runner.invoke(
            main,
            ["validate", schema_v2_path, schema_v3_path, "--no-fail-on-breaking"],
        )

        # Should not fail even with breaking changes
        assert result.exit_code == 0

    def test_validate_json_format(self, runner, schema_v1_path, schema_v2_path):
        """Test validate with JSON format."""
        result = runner.invoke(
            main, ["validate", schema_v1_path, schema_v2_path, "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "is_backward_compatible" in data

    def test_validate_strict_mode(self, runner, schema_v1_path, schema_v2_path):
        """Test validate with strict mode."""
        result = runner.invoke(
            main, ["validate", schema_v1_path, schema_v2_path, "--strict"]
        )

        # With strict mode, some forward compatibility issues may be flagged
        assert result.exit_code == 0  # Still backward compatible


class TestMigrateCommand:
    """Tests for migrate command."""

    def test_migrate_python(self, runner, schema_v1_path, schema_v2_path):
        """Test migrate command generating Python script."""
        result = runner.invoke(
            main, ["migrate", schema_v1_path, schema_v2_path, "--language", "python"]
        )

        assert result.exit_code == 0
        assert "def migrate" in result.output

    def test_migrate_javascript(self, runner, schema_v1_path, schema_v2_path):
        """Test migrate command generating JavaScript script."""
        result = runner.invoke(
            main,
            ["migrate", schema_v1_path, schema_v2_path, "--language", "javascript"],
        )

        assert result.exit_code == 0
        assert "function migrate" in result.output

    def test_migrate_with_output_file(
        self, runner, schema_v1_path, schema_v2_path, tmp_path
    ):
        """Test migrate output to file."""
        output_file = tmp_path / "migrate.py"
        result = runner.invoke(
            main,
            [
                "migrate",
                schema_v1_path,
                schema_v2_path,
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "def migrate" in content


class TestInfoCommand:
    """Tests for info command."""

    def test_info_basic(self, runner, schema_v1_path):
        """Test basic info command."""
        result = runner.invoke(main, ["info", schema_v1_path])

        assert result.exit_code == 0
        assert "Schema:" in result.output
        assert "Properties:" in result.output

    def test_info_shows_properties(self, runner, schema_v1_path):
        """Test that info shows properties."""
        result = runner.invoke(main, ["info", schema_v1_path])

        assert result.exit_code == 0
        assert "sample_id" in result.output
        assert "patient_id" in result.output


class TestVersionOption:
    """Tests for version option."""

    def test_version(self, runner):
        """Test --version option."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "jsonschema-changelog" in result.output
        assert "0.1.0" in result.output
