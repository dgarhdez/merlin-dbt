from merlin.renderer import build_id_map, render_mermaid


def _node(resource_type: str, name: str, source_name: str = "") -> dict:
    n = {"resource_type": resource_type, "name": name}
    if source_name:
        n["source_name"] = source_name
    return n


# --- build_id_map ---


def test_id_map_sanitizes_dots():
    m = build_id_map(["model.pkg.name"])
    assert m["model.pkg.name"] == "model__pkg__name"


def test_id_map_sanitizes_hyphens():
    m = build_id_map(["model.pkg.my-model"])
    assert m["model.pkg.my-model"] == "model__pkg__my_model"


def test_id_map_collision_suffix():
    m = build_id_map(["model.pkg.foo_bar", "model.pkg.foo-bar"])
    ids = set(m.values())
    # Both should have distinct IDs
    assert len(ids) == 2
    assert "model__pkg__foo_bar" in ids
    assert "model__pkg__foo_bar_2" in ids


# --- render_mermaid ---


def test_single_model_rectangle():
    nodes = {"model.pkg.orders": _node("model", "orders")}
    out = render_mermaid(nodes, [], raw=True)
    assert 'model__pkg__orders["orders"]' in out


def test_source_stadium_shape():
    nodes = {"source.pkg.raw.orders": _node("source", "orders", "raw")}
    out = render_mermaid(nodes, [], raw=True)
    assert 'source__pkg__raw__orders(["raw.orders"])' in out


def test_seed_hexagon_shape():
    nodes = {"seed.pkg.country_codes": _node("seed", "country_codes")}
    out = render_mermaid(nodes, [], raw=True)
    assert 'seed__pkg__country_codes{"country_codes"}' in out


def test_snapshot_hexagon_shape():
    nodes = {"model.pkg.orders_snap": _node("snapshot", "orders_snap")}
    out = render_mermaid(nodes, [], raw=True)
    assert 'model__pkg__orders_snap{"orders_snap"}' in out


def test_edge_arrow():
    nodes = {
        "source.pkg.raw.o": _node("source", "o", "raw"),
        "model.pkg.stg": _node("model", "stg"),
    }
    edges = [("source.pkg.raw.o", "model.pkg.stg")]
    out = render_mermaid(nodes, edges, raw=True)
    assert "source__pkg__raw__o --> model__pkg__stg" in out


def test_model_with_hyphen_label():
    nodes = {"model.pkg.my-model": _node("model", "my-model")}
    out = render_mermaid(nodes, [], raw=True)
    assert 'model__pkg__my_model["my-model"]' in out


def test_raw_false_adds_fence():
    nodes = {"model.pkg.x": _node("model", "x")}
    out = render_mermaid(nodes, [], raw=False)
    assert out.startswith("```mermaid\n")
    assert out.strip().endswith("```")


def test_raw_true_no_fence():
    nodes = {"model.pkg.x": _node("model", "x")}
    out = render_mermaid(nodes, [], raw=True)
    assert out.startswith("flowchart LR")
    assert "```" not in out


def test_collision_ids_are_distinct():
    nodes = {
        "model.pkg.foo_bar": _node("model", "foo_bar"),
        "model.pkg.foo-bar": _node("model", "foo-bar"),
    }
    out = render_mermaid(nodes, [], raw=True)
    assert "model__pkg__foo_bar[" in out
    assert "model__pkg__foo_bar_2[" in out


def test_empty_nodes():
    out = render_mermaid({}, [], raw=True)
    assert out.strip() == "flowchart LR"
