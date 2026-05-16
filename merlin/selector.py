import re
from collections import deque


class SelectorParseError(Exception):
    pass


class ModelNotFoundError(Exception):
    pass


_SELECTOR_RE = re.compile(r"^(\+?)([A-Za-z0-9_\-\.]+)(\+?)$")


def parse_selector(selector: str) -> tuple[str, bool, bool]:
    m = _SELECTOR_RE.match(selector.strip())
    if not m:
        raise SelectorParseError(
            f"Invalid selector '{selector}'. "
            "Supported patterns: model, +model, model+, +model+"
        )
    upstream_prefix, name, downstream_suffix = m.groups()
    return name, bool(upstream_prefix), bool(downstream_suffix)


def apply_selector(
    selector: str,
    nodes: dict,
    edges: list[tuple[str, str]],
) -> tuple[dict, list]:
    model_name, include_upstream, include_downstream = parse_selector(selector)

    name_to_uids: dict[str, list[str]] = {}
    for uid, node in nodes.items():
        n = node.get("name", "")
        name_to_uids.setdefault(n, []).append(uid)

    if model_name not in name_to_uids:
        raise ModelNotFoundError(
            f"Model '{model_name}' not found in manifest. "
            "Check the name or run 'dbt compile' to refresh manifest.json."
        )

    target_uids = set(name_to_uids[model_name])

    # Build adjacency for BFS
    # upstream: child → parents  (following edges backward)
    # downstream: parent → children (following edges forward)
    upstream_adj: dict[str, list[str]] = {uid: [] for uid in nodes}
    downstream_adj: dict[str, list[str]] = {uid: [] for uid in nodes}
    for src, dst in edges:
        upstream_adj[dst].append(src)
        downstream_adj[src].append(dst)

    collected: set[str] = set(target_uids)

    if include_upstream:
        queue: deque[str] = deque(target_uids)
        while queue:
            uid = queue.popleft()
            for parent in upstream_adj.get(uid, []):
                if parent not in collected:
                    collected.add(parent)
                    queue.append(parent)

    if include_downstream:
        queue = deque(target_uids)
        while queue:
            uid = queue.popleft()
            for child in downstream_adj.get(uid, []):
                if child not in collected:
                    collected.add(child)
                    queue.append(child)

    subgraph_nodes = {uid: nodes[uid] for uid in collected}
    subgraph_edges = [
        (src, dst) for src, dst in edges if src in collected and dst in collected
    ]

    return subgraph_nodes, subgraph_edges
