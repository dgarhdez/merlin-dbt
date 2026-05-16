from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from merlin.manifest import node_label


def build_id_map(uids: Iterable[str]) -> dict[str, str]:
    uid_list = list(uids)
    base_ids: dict[str, str] = {}
    for uid in uid_list:
        base_ids[uid] = uid.replace(".", "__").replace("-", "_")

    # Detect collisions and append _2, _3, ... to duplicates
    seen: dict[str, int] = {}
    id_map: dict[str, str] = {}
    for uid in sorted(uid_list):  # sort for deterministic assignment of suffixes
        base = base_ids[uid]
        if base not in seen:
            seen[base] = 0
            id_map[uid] = base
        else:
            seen[base] += 1
            id_map[uid] = f"{base}_{seen[base] + 1}"

    return id_map


def render_mermaid(nodes: dict, edges: list[tuple[str, str]], raw: bool = False) -> str:
    id_map = build_id_map(nodes.keys())

    lines: list[str] = ["flowchart LR"]

    for uid in sorted(nodes.keys()):
        node = nodes[uid]
        mid = id_map[uid]
        label = node_label(uid, node)
        resource_type = node.get("resource_type", "model")

        if resource_type == "source":
            lines.append(f'  {mid}(["{label}"])')
        elif resource_type in ("seed", "snapshot"):
            lines.append(f'  {mid}{{"{label}"}}')
        else:
            lines.append(f'  {mid}["{label}"]')

    for src, dst in edges:
        lines.append(f"  {id_map[src]} --> {id_map[dst]}")

    diagram = "\n".join(lines) + "\n"

    if raw:
        return diagram
    return f"```mermaid\n{diagram}```\n"
