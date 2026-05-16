# merlin

dbt lineage CLI — outputs Mermaid flowchart diagrams from `manifest.json`.

```
merlin +my_model+
```

Pipe the output into a GitHub PR description, embed it in documentation, or let an AI agent include it automatically.

## Installation

**curl (recommended)**

```bash
curl -LsSf https://raw.githubusercontent.com/dgarhdez/merlin-dbt/main/install.sh | sh
```

**npm**

```bash
npm install -g merlin-dbt
```

**pip / uv**

```bash
pip install merlin-dbt
# or
uv tool install merlin-dbt
```

## Usage

```bash
# Exact model only
merlin my_model

# Model and all upstream ancestors
merlin +my_model

# Model and all downstream descendants
merlin my_model+

# Full upstream + downstream subgraph
merlin +my_model+

# Use a specific dbt project directory
merlin +my_model+ --project-dir /path/to/dbt_project

# Emit raw Mermaid syntax (no fence, for scripting)
merlin +my_model+ --raw
```

### Selector patterns

| Pattern | Meaning |
|---------|---------|
| `model` | Exact match only |
| `+model` | Model and all upstream ancestors |
| `model+` | Model and all downstream descendants |
| `+model+` | Model, all ancestors, and all descendants |

Traversal terminates at `source()` nodes. Sources have no upstream ancestors in the manifest and are treated as roots.

### Node shapes in the diagram

| Resource type | Mermaid shape |
|---------------|---------------|
| model | rectangle |
| source | stadium |
| seed | hexagon |
| snapshot | hexagon |

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | User input error (model not found, invalid selector) |
| 2 | Environment error (manifest.json not found or invalid JSON) |

## Requirements

- Python ≥ 3.10
- A dbt project with a current `manifest.json` in `target/` (run `dbt compile` first)
- dbt Core 1.0+ (manifest schema v9+)

## Known limitations

**Code review workflow:** `merlin` reads the `manifest.json` in your local `target/` directory. When reviewing someone else's PR, your manifest reflects your own branch — not the PR author's. To see the PR author's lineage, check out their branch and run `dbt compile` first.

**Large subgraphs:** Selecting a highly connected model with `+model+` may produce a diagram with many nodes. GitHub's Mermaid renderer may clip very large diagrams. Use a more specific selector to limit scope.

## Example: GitHub Actions

```yaml
- name: Add lineage diagram to PR
  run: |
    DIAGRAM=$(merlin +${{ env.CHANGED_MODEL }}+)
    gh pr comment ${{ github.event.pull_request.number }} --body "$DIAGRAM"
```

## License

MIT
