"""
CLI Entrypoint shim for compatibility with PLAN.md references.
"""
from pathlib import Path
import sys

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from nova.cli import cli

if __name__ == "__main__":
    cli()
