"""
Tests for CLI commands.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner
from clearstone.cli.main import cli


class TestCLINewPolicy:
    """Test suite for 'new-policy' CLI command."""

    def test_cli_new_policy_creates_file(self, tmp_path):
        """Test that 'new-policy' command successfully creates a policy file."""
        runner = CliRunner()
        policy_name = "test_spending_limit"

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ['new-policy', policy_name, '--priority=100', '--dir=my_policies'])

            assert result.exit_code == 0
            assert "Successfully created policy file" in result.output

            expected_file = Path(td) / "my_policies" / "test_spending_limit_policy.py"
            assert expected_file.exists()

            content = expected_file.read_text()
            assert f'@Policy(name="{policy_name}", priority=100)' in content
            assert f"def {policy_name}_policy(context: PolicyContext)" in content

    def test_cli_new_policy_default_directory(self, tmp_path):
        """Test that default directory 'policies' is used when not specified."""
        runner = CliRunner()
        policy_name = "default_dir_policy"

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ['new-policy', policy_name])

            assert result.exit_code == 0

            expected_file = Path(td) / "policies" / "default_dir_policy_policy.py"
            assert expected_file.exists()

    def test_cli_new_policy_handles_existing_file(self, tmp_path):
        """Test that the command fails if the file exists and --force is not used."""
        runner = CliRunner()
        policy_name = "duplicate_policy"

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(cli, ['new-policy', policy_name])

            result = runner.invoke(cli, ['new-policy', policy_name])

            assert result.exit_code == 0
            assert "already exists" in result.output

    def test_cli_new_policy_force_overwrites_existing_file(self, tmp_path):
        """Test that --force successfully overwrites an existing file."""
        runner = CliRunner()
        policy_name = "overwritten_policy"

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            initial_result = runner.invoke(cli, ['new-policy', policy_name, '--priority=1'])
            assert "priority=1" in (Path(td) / "policies" / "overwritten_policy_policy.py").read_text()

            overwrite_result = runner.invoke(cli, ['new-policy', policy_name, '--priority=99', '--force'])

            assert overwrite_result.exit_code == 0
            assert "Successfully created policy file" in overwrite_result.output

            final_content = (Path(td) / "policies" / "overwritten_policy_policy.py").read_text()
            assert "priority=99" in final_content

    def test_cli_new_policy_sanitizes_name(self, tmp_path):
        """Test that policy names with hyphens are properly sanitized."""
        runner = CliRunner()
        policy_name = "my-hyphenated-policy"

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ['new-policy', policy_name])

            assert result.exit_code == 0

            expected_file = Path(td) / "policies" / "my_hyphenated_policy_policy.py"
            assert expected_file.exists()

            content = expected_file.read_text()
            assert "def my_hyphenated_policy_policy(context: PolicyContext)" in content

    def test_cli_new_policy_creates_nested_directories(self, tmp_path):
        """Test that nested directories are created if they don't exist."""
        runner = CliRunner()
        policy_name = "nested_policy"

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ['new-policy', policy_name, '--dir=nested/deep/policies'])

            assert result.exit_code == 0

            expected_file = Path(td) / "nested" / "deep" / "policies" / "nested_policy_policy.py"
            assert expected_file.exists()

    def test_cli_new_policy_default_priority(self, tmp_path):
        """Test that default priority of 0 is used when not specified."""
        runner = CliRunner()
        policy_name = "default_priority"

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ['new-policy', policy_name])

            assert result.exit_code == 0

            content = (Path(td) / "policies" / "default_priority_policy.py").read_text()
            assert "priority=0" in content

    def test_cli_new_policy_includes_template_content(self, tmp_path):
        """Test that generated file contains expected template content."""
        runner = CliRunner()
        policy_name = "template_test"

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ['new-policy', policy_name])

            assert result.exit_code == 0

            content = (Path(td) / "policies" / "template_test_policy.py").read_text()
            assert "from clearstone import Policy, ALLOW, BLOCK, Decision" in content
            assert "from clearstone.core.context import PolicyContext" in content
            assert "[TODO: Describe what this policy does.]" in content
            assert "return ALLOW" in content

