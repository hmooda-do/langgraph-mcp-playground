"""Point agents.yaml at the commit you just pushed:  git push && python scripts/pin_commit.py"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "agents.yaml"


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


sha = git("rev-parse", "HEAD")
git("fetch", "--quiet", "origin")
if not git("branch", "--remotes", "--contains", sha):
    sys.exit(f"{sha} isn't on origin yet. Push first.")
text = re.sub(r'(repo_sha:\s*)"?[0-9a-f]{40}"?', rf'\g<1>"{sha}"', SPEC.read_text())
SPEC.write_text(text)
print(f"pinned {sha}")
