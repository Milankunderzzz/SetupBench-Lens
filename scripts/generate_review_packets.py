from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from common import CONFIG, ROOT, load_json


PACKETS = ROOT / "dataset" / "annotations" / "workflow-review-packets"


def excerpt(path: Path, limit: int = 12000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return "<unavailable>"


def main() -> None:
    manifest = {row["id"]: row for row in load_json(CONFIG / "repositories.frozen.json")["repositories"]}
    workflows = list(csv.DictReader((CONFIG / "workflows.csv").open(encoding="utf-8", newline="")))
    PACKETS.mkdir(parents=True, exist_ok=True)
    index_rows = []

    for workflow in workflows:
        repository = manifest[workflow["repository_id"]]
        root = ROOT / "dataset" / "repos" / repository["id"]
        readme = next((path for path in root.iterdir() if path.is_file() and path.name.lower().startswith("readme")), None)
        readme_text = excerpt(readme) if readme else "<no root README>"
        packet = f"""# Workflow Review: {repository['repository']}

- Repository ID: `{repository['id']}`
- Commit: `{repository['commitSha']}`
- Stratum: `{repository['stratum']}`
- Candidate source: `{workflow['workflow_source']}`

## Candidate Workflow

```sh
{workflow['bootstrap_command']}
{workflow['primary_command']}
```

Health criterion: {workflow['health_criterion']}

## Reviewer Decision

- [ ] The source is the shortest documented local-development workflow.
- [ ] Commands are valid at the pinned commit.
- [ ] No credential, paid service, private source, or host secret is required.
- [ ] The health criterion proves a ready state or a precise blocking point.

Decision: `approve` / `revise` / `exclude`  
Reviewer ID:  
Date:  
Rationale:

## Root README Excerpt

```text
{readme_text}
```
"""
        path = PACKETS / f"{repository['id']}.md"
        path.write_text(packet, encoding="utf-8")
        digest = hashlib.sha256(packet.encode("utf-8")).hexdigest()
        index_rows.append((repository["id"], path.relative_to(ROOT).as_posix(), digest, "pending"))

    with (PACKETS / "index.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["repository_id", "packet_path", "packet_sha256", "review_status"])
        writer.writerows(index_rows)
    print(f"Generated {len(index_rows)} blinded workflow review packets in {PACKETS}")


if __name__ == "__main__":
    main()

