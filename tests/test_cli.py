import subprocess
import sys
from pathlib import Path

from click.testing import CliRunner

from merlin.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"


def make_project(tmp_path: Path, fixture: str = "manifest_v12.json") -> Path:
    target = tmp_path / "target"
    target.mkdir()
    (target / "manifest.json").write_text((FIXTURES / fixture).read_text())
    return tmp_path


# --- Happy paths ---


def test_basic_selector_outputs_flowchart(tmp_path):
    project = make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["stg_orders", "--project-dir", str(project)])
    assert result.exit_code == 0
    assert "flowchart LR" in result.output
    assert result.output.startswith("```mermaid")


def test_raw_flag_no_fence(tmp_path):
    project = make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["stg_orders", "--project-dir", str(project), "--raw"])
    assert result.exit_code == 0
    assert result.output.startswith("flowchart LR")
    assert "```" not in result.output


def test_project_dir_flag(tmp_path):
    project = make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["orders", "--project-dir", str(project)])
    assert result.exit_code == 0
    assert "flowchart LR" in result.output


def test_upstream_selector(tmp_path):
    project = make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["+orders", "--project-dir", str(project)])
    assert result.exit_code == 0
    assert "stg_orders" in result.output
    assert "raw.orders" in result.output


# --- Error paths ---


def test_manifest_not_found_exits_2(tmp_path):
    # Use subprocess to verify stdout/stderr separation (CliRunner 8.3.x merges streams)
    merlin_bin = Path(sys.executable).parent / "merlin"
    proc = subprocess.run(
        [str(merlin_bin), "orders", "--project-dir", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout == ""  # nothing on stdout (R5)
    assert "manifest.json not found" in proc.stderr


def test_model_not_found_exits_1(tmp_path):
    project = make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["nonexistent_model", "--project-dir", str(project)])
    assert result.exit_code == 1


def test_invalid_selector_exits_1(tmp_path):
    project = make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["++orders", "--project-dir", str(project)])
    assert result.exit_code == 1


# --- Integration ---


def test_full_pipeline_stg_orders(tmp_path):
    project = make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["+stg_orders+", "--project-dir", str(project), "--raw"])
    assert result.exit_code == 0
    assert "stg_orders" in result.output
    assert "raw.orders" in result.output


def test_help_lists_selector_and_exit_codes():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "SELECTOR" in result.output
    assert "--project-dir" in result.output
    assert "--raw" in result.output
    assert "Exit codes" in result.output
