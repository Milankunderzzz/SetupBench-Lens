from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess

from common import CONFIG, REPOS, command_output, load_json


MANIFEST = CONFIG / "repositories.frozen.json"


def run(args: list[str], *, cwd=None) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def remove_tree(path) -> None:
    def make_writable(function, value, _error):
        os.chmod(value, stat.S_IWRITE)
        function(value)

    shutil.rmtree(path, onexc=make_writable)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    manifest = load_json(MANIFEST)
    REPOS.mkdir(parents=True, exist_ok=True)

    for index, repository in enumerate(manifest["repositories"], start=1):
        destination = REPOS / repository["id"]
        if args.refresh and destination.exists():
            remove_tree(destination)

        if (destination / ".git").exists():
            try:
                actual = command_output(["git", "rev-parse", "HEAD"], cwd=destination)
            except subprocess.CalledProcessError:
                remove_tree(destination)
            else:
                if actual != repository["commitSha"]:
                    raise RuntimeError(f"Commit mismatch for {repository['id']}: {actual}")
                print(f"[{index:02d}/50] existing {repository['id']} {actual[:12]}")
                continue

        destination.mkdir(parents=True, exist_ok=True)
        run(["git", "init", "-q"], cwd=destination)
        run(["git", "remote", "add", "origin", repository["url"]], cwd=destination)
        run(
            ["git", "-c", "protocol.version=2", "fetch", "--depth", "1", "--filter=blob:none", "origin", repository["commitSha"]],
            cwd=destination,
        )
        run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=destination)
        actual = command_output(["git", "rev-parse", "HEAD"], cwd=destination)
        if actual != repository["commitSha"]:
            raise RuntimeError(f"Commit mismatch for {repository['id']}: {actual}")
        print(f"[{index:02d}/50] cloned {repository['id']} {actual[:12]}")


if __name__ == "__main__":
    main()
