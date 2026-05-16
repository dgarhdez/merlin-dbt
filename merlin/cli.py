import sys
from pathlib import Path

import click


@click.command(
    help="Output a Mermaid flowchart of dbt model lineage to stdout.",
    epilog="""\b
SELECTOR patterns:

  model       exact match only
  +model      model and all upstream ancestors
  model+      model and all downstream descendants
  +model+     model, all ancestors, and all descendants

Exit codes:

  0  Success
  1  User input error (model not found, invalid selector)
  2  Environment error (manifest.json not found or invalid)
""",
)
@click.argument("selector")
@click.option(
    "--project-dir",
    default=None,
    type=click.Path(exists=False, file_okay=False, path_type=Path),
    help="dbt project root (default: current directory)",
)
@click.option(
    "--raw",
    is_flag=True,
    default=False,
    help="Emit plain Mermaid syntax without a ```mermaid fence",
)
def cli(selector: str, project_dir: Path | None, raw: bool) -> None:
    from merlin.manifest import ManifestNotFoundError, ManifestParseError, parse_manifest
    from merlin.renderer import render_mermaid
    from merlin.selector import ModelNotFoundError, SelectorParseError, apply_selector

    project_path = project_dir if project_dir is not None else Path.cwd()

    try:
        nodes, edges = parse_manifest(project_path)
    except ManifestNotFoundError as exc:
        click.echo(str(exc), err=True)
        sys.exit(2)
    except ManifestParseError as exc:
        click.echo(str(exc), err=True)
        sys.exit(2)

    try:
        subgraph_nodes, subgraph_edges = apply_selector(selector, nodes, edges)
    except SelectorParseError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    except ModelNotFoundError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    click.echo(render_mermaid(subgraph_nodes, subgraph_edges, raw=raw), nl=False)
