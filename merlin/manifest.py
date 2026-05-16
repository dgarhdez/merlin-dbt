import json
import sys
from pathlib import Path


class ManifestNotFoundError(Exception):
    pass


class ManifestParseError(Exception):
    pass


_INCLUDED_RESOURCE_TYPES = {"model", "source", "seed", "snapshot"}

_MIN_SCHEMA_VERSION = 9


def _schema_version(manifest: dict) -> int | None:
    url = manifest.get("metadata", {}).get("dbt_schema_version", "")
    # e.g. "https://schemas.getdbt.com/dbt/manifest/v12/manifest.json"
    for part in reversed(url.split("/")):
        if part.startswith("v") and part[1:].isdigit():
            return int(part[1:])
    return None


def node_label(uid: str, node: dict) -> str:
    resource_type = node.get("resource_type", "")
    if resource_type == "source":
        source_name = node.get("source_name", "")
        name = node.get("name", uid)
        return f"{source_name}.{name}" if source_name else name
    return node.get("name", uid)


def parse_manifest(project_dir: Path) -> tuple[dict, list]:
    manifest_path = project_dir / "target" / "manifest.json"

    if not manifest_path.exists():
        raise ManifestNotFoundError(
            f"manifest.json not found at {manifest_path}. Run 'dbt compile' first."
        )

    try:
        with manifest_path.open() as f:
            manifest = json.load(f)
    except json.JSONDecodeError as exc:
        raise ManifestParseError(
            f"manifest.json is not valid JSON: {exc}"
        ) from exc

    version = _schema_version(manifest)
    if version is not None and version < _MIN_SCHEMA_VERSION:
        print(
            f"Warning: manifest schema version v{version} is older than v{_MIN_SCHEMA_VERSION} "
            "(dbt Core 1.0). Attempting to parse anyway.",
            file=sys.stderr,
        )

    raw_nodes: dict = manifest.get("nodes", {})
    raw_sources: dict = manifest.get("sources", {})

    nodes: dict = {}
    for uid, node in {**raw_nodes, **raw_sources}.items():
        if node.get("resource_type") in _INCLUDED_RESOURCE_TYPES:
            nodes[uid] = node

    allowed_uids = set(nodes.keys())

    edges: list[tuple[str, str]] = []
    for uid, node in nodes.items():
        if node.get("resource_type") == "source":
            continue
        for dep_uid in node.get("depends_on", {}).get("nodes", []):
            if dep_uid in allowed_uids:
                edges.append((dep_uid, uid))

    return nodes, edges
