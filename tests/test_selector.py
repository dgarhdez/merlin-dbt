import pytest

from merlin.selector import (
    ModelNotFoundError,
    SelectorParseError,
    apply_selector,
    parse_selector,
)

# --- parse_selector ---


def test_parse_exact():
    assert parse_selector("my_model") == ("my_model", False, False)


def test_parse_upstream():
    assert parse_selector("+my_model") == ("my_model", True, False)


def test_parse_downstream():
    assert parse_selector("my_model+") == ("my_model", False, True)


def test_parse_both():
    assert parse_selector("+my_model+") == ("my_model", True, True)


def test_parse_invalid_double_prefix():
    with pytest.raises(SelectorParseError, match="Invalid selector"):
        parse_selector("++my_model")


def test_parse_invalid_empty():
    with pytest.raises(SelectorParseError):
        parse_selector("")


# --- apply_selector helpers ---

# Graph: source_a -> stg -> orders -> snapshot_orders
#                 -> stg_b -> orders

NODES = {
    "source.pkg.raw.a": {"name": "a", "resource_type": "source", "source_name": "raw"},
    "source.pkg.raw.b": {"name": "b", "resource_type": "source", "source_name": "raw"},
    "model.pkg.stg": {"name": "stg", "resource_type": "model"},
    "model.pkg.stg_b": {"name": "stg_b", "resource_type": "model"},
    "model.pkg.orders": {"name": "orders", "resource_type": "model"},
    "model.pkg.orders_snapshot": {"name": "orders_snapshot", "resource_type": "snapshot"},
}

EDGES = [
    ("source.pkg.raw.a", "model.pkg.stg"),
    ("source.pkg.raw.b", "model.pkg.stg_b"),
    ("model.pkg.stg", "model.pkg.orders"),
    ("model.pkg.stg_b", "model.pkg.orders"),
    ("model.pkg.orders", "model.pkg.orders_snapshot"),
]


# --- Happy paths ---


def test_exact_match_single_node():
    sub_nodes, sub_edges = apply_selector("orders", NODES, EDGES)
    assert set(sub_nodes.keys()) == {"model.pkg.orders"}
    assert sub_edges == []


def test_upstream_includes_ancestors():
    sub_nodes, sub_edges = apply_selector("+orders", NODES, EDGES)
    assert "model.pkg.orders" in sub_nodes
    assert "model.pkg.stg" in sub_nodes
    assert "model.pkg.stg_b" in sub_nodes
    assert "source.pkg.raw.a" in sub_nodes
    assert "source.pkg.raw.b" in sub_nodes
    # snapshot is downstream — should NOT appear
    assert "model.pkg.orders_snapshot" not in sub_nodes


def test_downstream_includes_descendants():
    sub_nodes, sub_edges = apply_selector("orders+", NODES, EDGES)
    assert "model.pkg.orders" in sub_nodes
    assert "model.pkg.orders_snapshot" in sub_nodes
    # upstream should NOT appear
    assert "model.pkg.stg" not in sub_nodes


def test_both_directions():
    sub_nodes, sub_edges = apply_selector("+orders+", NODES, EDGES)
    for uid in NODES:
        assert uid in sub_nodes


def test_multi_hop_ancestry():
    # Select stg, go upstream: should include source_a but not source_b/stg_b/orders
    sub_nodes, sub_edges = apply_selector("+stg", NODES, EDGES)
    assert "model.pkg.stg" in sub_nodes
    assert "source.pkg.raw.a" in sub_nodes
    assert "source.pkg.raw.b" not in sub_nodes
    assert "model.pkg.orders" not in sub_nodes


# --- Edge cases ---


def test_no_upstream_returns_single_node():
    # source has no upstream
    sub_nodes, sub_edges = apply_selector("+a", NODES, EDGES)
    assert set(sub_nodes.keys()) == {"source.pkg.raw.a"}
    assert sub_edges == []


def test_no_downstream_returns_single_node():
    sub_nodes, sub_edges = apply_selector("orders_snapshot+", NODES, EDGES)
    assert set(sub_nodes.keys()) == {"model.pkg.orders_snapshot"}
    assert sub_edges == []


def test_source_appears_but_no_further_upstream():
    sub_nodes, sub_edges = apply_selector("+stg", NODES, EDGES)
    assert "source.pkg.raw.a" in sub_nodes
    # source.pkg.raw.a has no parents — only stg and raw.a in result
    assert len(sub_nodes) == 2


# --- Error paths ---


def test_model_not_found():
    with pytest.raises(ModelNotFoundError, match="'ghost'"):
        apply_selector("ghost", NODES, EDGES)


def test_invalid_selector_format():
    with pytest.raises(SelectorParseError):
        apply_selector("++orders", NODES, EDGES)
