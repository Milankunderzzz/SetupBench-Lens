from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
import time
import uuid
from pathlib import Path

from common import CONFIG, LOGS, REPOS, ROOT, redact, sha256_text


RESULTS = ROOT / "dataset" / "direct-executions.jsonl"


def image_digest(image: str) -> str | None:
    subprocess.run(["docker", "pull", image], check=True)
    output = subprocess.check_output(
        ["docker", "image", "inspect", image, "--format", "{{index .RepoDigests 0}}"],
        text=True,
        encoding="utf-8",
    ).strip()
    return output or None


def execute(row: dict[str, str], *, probe: bool) -> dict:
    repository_id = row["repository_id"]
    source = REPOS / repository_id
    image = row["container_image"]
    digest = image_digest(image)
    command = (
        "set -eu; cp -a /source/. /work/repository; cd /work/repository/" + row["working_directory"].lstrip("./") + "; "
        "printf '\\n<SETUPBENCH_PHASE bootstrap>\\n'; " + row["bootstrap_command"] + "; "
        "printf '\\n<SETUPBENCH_PHASE primary>\\n'; " + row["primary_command"]
    )
    docker_command = [
        "docker", "run", "--rm", "--network", "bridge",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
        "--pids-limit", "512", "--memory", "3g", "--cpus", "2",
        "--tmpfs", "/work:rw,exec,nosuid,size=4g",
        "--mount", f"type=bind,src={source},dst=/source,readonly",
        "--workdir", "/work", image, "sh", "-lc", command,
    ]
    started = dt.datetime.now(dt.timezone.utc)
    begin = time.perf_counter()
    timed_out = False
    try:
        completed = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=int(row["timeout_seconds"]),
        )
        exit_code = completed.returncode
        output = completed.stdout + "\n" + completed.stderr
    except subprocess.TimeoutExpired as error:
        timed_out = True
        exit_code = None
        output = (error.stdout or "") + "\n" + (error.stderr or "")
        subprocess.run(["docker", "ps", "-q", "--filter", f"ancestor={image}"], capture_output=True)

    duration_ms = round((time.perf_counter() - begin) * 1000)
    clean = redact(output)
    LOGS.mkdir(parents=True, exist_ok=True)
    execution_id = f"exec-{repository_id}-{uuid.uuid4().hex[:10]}"
    log_path = LOGS / f"{execution_id}.log"
    log_path.write_text(clean, encoding="utf-8")
    return {
        "execution_id": execution_id,
        "repository_id": repository_id,
        "execution_kind": "unreviewed_probe" if probe else "approved_workflow",
        "image_reference": image,
        "image_digest": digest,
        "started_at": started.isoformat(),
        "duration_ms": duration_ms,
        "timed_out": timed_out,
        "exit_code": exit_code,
        "command_text": f"{row['bootstrap_command']} && {row['primary_command']}",
        "log_path": log_path.relative_to(ROOT).as_posix(),
        "log_sha256": sha256_text(clean),
        "status": "timeout" if timed_out else ("passed" if exit_code == 0 else "failed"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true", help="Run unreviewed candidates without treating them as ground truth")
    parser.add_argument("--repository", action="append", default=[])
    args = parser.parse_args()
    rows = list(csv.DictReader((CONFIG / "workflows.csv").open(encoding="utf-8", newline="")))
    if args.repository:
        rows = [row for row in rows if row["repository_id"] in set(args.repository)]
    if not args.probe:
        pending = [row["repository_id"] for row in rows if row["approval_status"] != "approved"]
        if pending:
            raise SystemExit(f"Refusing execution: {len(pending)} workflows are not approved. Use --probe only for non-ground-truth diagnostics.")

    with RESULTS.open("a", encoding="utf-8") as handle:
        for index, row in enumerate(rows, start=1):
            result = execute(row, probe=args.probe)
            handle.write(json.dumps(result, ensure_ascii=True) + "\n")
            handle.flush()
            print(f"[{index:02d}/{len(rows)}] {row['repository_id']}: {result['status']} in {result['duration_ms']} ms")


if __name__ == "__main__":
    main()

