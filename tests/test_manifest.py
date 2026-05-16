import json
import sys
from pathlib import Path

import pytest

from merlin.manifest import (
    ManifestNotFoundError,
    ManifestParseError,
    node_label,
    parse_manifest,
)

FIXTURES = Path(__file__).parent / "fixtures"


def make_project_dir(tmp_path: Path, fixture_name: str) -> Path:
    target = tmp_path / "target"
    target.mkdir()
    src = FIXTURES / fixture_name
    (target / "manifest.json").write_text(src.read_text())
    return tmp_path


# --- Happy paths ---


def test_v12_returns_nodes_and_edges(tmp_path):
    project_dir = make_project_dir(tmp_path, "manifest_v12.json")
    nodes, edges = parse_manifest(project_dir)

    assert "model.jaffle_shop.stg_orders" in nodes
    assert "model.jaffle_shop.orders" in nodes
    assert "source.jaffle_shop.raw.orders" in nodes
    assert "seed.jaffle_shop.country_codes" in nodes
    assert "model.jaffle_shop.orders_snapshot" in nodes
    # test and analysis nodes excluded
    assert "test.jaffle_shop.not_null_orders_id" not in nodes
    assert "analysis.jaffle_shop.revenue_analysis" not in nodes

    # stg_orders depends on source
    assert ("source.jaffle_shop.raw.orders", "model.jaffle_shop.stg_orders") in edges


def test_multiple_upstream_deps(tmp_path):
    project_dir = make_project_dir(tmp_path, "manifest_v12.json")
    nodes, edges = parse_manifest(project_dir)

    dst = "model.jaffle_shop.orders"
    incoming = [src for src, d in edges if d == dst]
    assert "model.jaffle_shop.stg_orders" in incoming
    assert "model.jaffle_shop.stg_customers" in incoming
    assert "seed.jaffle_shop.country_codes" in incoming


def test_source_has_no_incoming_edges(tmp_path):
    """Sources are upstream roots — nothing should depend on a source."""
    project_dir = make_project_dir(tmp_path, "manifest_v12.json")
    nodes, edges = parse_manifest(project_dir)

    src_uid = "source.jaffle_shop.raw.orders"
    assert src_uid in nodes
    # Sources have outgoing edges (to models that ref them), but no incoming edges
    incoming = [s for s, dst in edges if dst == src_uid]
    assert incoming == []


def test_seed_present_in_nodes(tmp_path):
    project_dir = make_project_dir(tmp_path, "manifest_v12.json")
    nodes, edges = parse_manifest(project_dir)

    assert "seed.jaffle_shop.country_codes" in nodes
    seed = nodes["seed.jaffle_shop.country_codes"]
    assert seed["resource_type"] == "seed"
    # orders model depends on seed
    assert ("seed.jaffle_shop.country_codes", "model.jaffle_shop.orders") in edges


def test_snapshot_present_in_nodes(tmp_path):
    project_dir = make_project_dir(tmp_path, "manifest_v12.json")
    nodes, edges = parse_manifest(project_dir)

    snap_uid = "model.jaffle_shop.orders_snapshot"
    assert snap_uid in nodes
    assert nodes[snap_uid]["resource_type"] == "snapshot"
    assert ("model.jaffle_shop.orders", snap_uid) in edges


def test_v9_manifest_parses_correctly(tmp_path):
    project_dir = make_project_dir(tmp_path, "manifest_v9.json")
    nodes, edges = parse_manifest(project_dir)

    assert "model.shop.stg_orders" in nodes
    assert "model.shop.orders" in nodes
    assert "source.shop.raw.orders" in nodes
    assert ("source.shop.raw.orders", "model.shop.stg_orders") in edges


# --- Edge cases ---


def test_single_model_no_deps(tmp_path):
    manifest = {
        "metadata": {"dbt_schema_version": "https://schemas.getdbt.com/dbt/manifest/v12/manifest.json"},
        "nodes": {
            "model.pkg.alone": {
                "unique_id": "model.pkg.alone",
                "name": "alone",
                "resource_type": "model",
                "depends_on": {"nodes": []},
            }
        },
        "sources": {},
    }
    target = tmp_path / "target"
    target.mkdir()
    (target / "manifest.json").write_text(json.dumps(manifest))
    nodes, edges = parse_manifest(tmp_path)

    assert len(nodes) == 1
    assert edges == []


def test_test_and_macro_nodes_excluded(tmp_path):
    project_dir = make_project_dir(tmp_path, "manifest_v12.json")
    nodes, edges = parse_manifest(project_dir)

    # No test or analysis nodes in result
    for uid in nodes:
        assert nodes[uid]["resource_type"] in ("model", "source", "seed", "snapshot")

    # No phantom edges to/from excluded types
    all_uids = set(nodes.keys())
    for src, dst in edges:
        assert src in all_uids
        assert dst in all_uids


# --- Error paths ---


def test_manifest_not_found_raises(tmp_path):
    with pytest.raises(ManifestNotFoundError, match="manifest.json not found"):
        parse_manifest(tmp_path)


def test_malformed_json_raises(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "manifest.json").write_text("{ not valid json }")
    with pytest.raises(ManifestParseError, match="not valid JSON"):
        parse_manifest(tmp_path)


def test_old_schema_version_warns_stderr(tmp_path, capsys):
    manifest = {
        "metadata": {"dbt_schema_version": "https://schemas.getdbt.com/dbt/manifest/v5/manifest.json"},
        "nodes": {},
        "sources": {},
    }
    target = tmp_path / "target"
    target.mkdir()
    (target / "manifest.json").write_text(json.dumps(manifest))
    parse_manifest(tmp_path)
    captured = capsys.readouterr()
    assert "Warning" in captured.err
    assert "v5" in captured.err


# --- node_label helper ---


def test_node_label_source():
    node = {"resource_type": "source", "source_name": "raw", "name": "orders"}
    assert node_label("source.pkg.raw.orders", node) == "raw.orders"


def test_node_label_model():
    node = {"resource_type": "model", "name": "stg_orders"}
    assert node_label("model.pkg.stg_orders", node) == "stg_orders"
