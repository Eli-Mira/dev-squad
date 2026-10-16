"""
DevSquad — 4-Agent Code Review Team

Usage:
  python dev_squad.py --target . --focus all --dry-run
  python dev_squad.py --target src/ --focus security
  python dev_squad.py --target . --scope "last-commit"
"""

import argparse
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal
from enum import Enum


class RiskTier(str, Enum):
    SAFE = "SAFE"
    CAREFUL = "CAREFUL"
    RISKY = "RISKY"
    BUG = "BUG"


@dataclass
class Finding:
    file: str
    line: int | None
    tier: RiskTier
    category: str  # reuse | quality | efficiency | altitude | security | design
    description: str
    suggested_fix: str
    confidence: float  # 0.0–1.0
    risk_desc: str = ""


@dataclass
class Report:
    target: str
    focus: str
    files_reviewed: int
    duration_seconds: float
    findings: list[Finding] = field(default_factory=list)

    def print(self):
        safe = [f for f in self.findings if f.tier == RiskTier.SAFE]
        careful = [f for f in self.findings if f.tier == RiskTier.CAREFUL]
        risky = [f for f in self.findings if f.tier == RiskTier.RISKY]
        bugs = [f for f in self.findings if f.tier == RiskTier.BUG]

        w = min(72, max(60, len(self.target) + 10))
        sep = "═" * w
        print(f"\n{sep}")
        print(f"  DEV SQUAD REPORT — {self.target}")
        print(f"  Focus: {self.focus} | Files reviewed: {self.files_reviewed}")
        print(f"  Time: {self.duration_seconds:.1f}s")
        print(sep)

        if bugs:
            print(f"\n⚠️  BUGS — {len(bugs)} potential correctness issues\n")
            for f in bugs:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                print(f"  [{loc}] {f.description}")
                if f.suggested_fix:
                    print(f"    → {f.suggested_fix}")

        if safe:
            print(f"\n🟢 SAFE — Auto-applicable ({len(safe)})\n")
            for f in safe[:5]:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                print(f"  [{loc}] {f.description}")
                print(f"    → {f.suggested_fix}")
            if len(safe) > 5:
                print(f"  ... and {len(safe) - 5} more")

        if careful:
            print(f"\n🟡 CAREFUL — Apply with verification ({len(careful)})\n")
            for f in careful[:5]:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                print(f"  [{loc}] {f.description}")
                print(f"    → {f.suggested_fix}")

        if risky:
            print(f"\n🔴 RISKY — Needs human review ({len(risky)})\n")
            for f in risky[:5]:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                print(f"  [{loc}] {f.description}")
                print(f"    → {f.risk_desc or f.suggested_fix}")


def scan_files(target: str, scope: str | None = None) -> list[Path]:
    """Collect source files to review."""
    t = Path(target)
    skip = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".tox"}

    if scope == "last-commit":
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True, text=True, cwd=t
            )
            if result.returncode == 0 and result.stdout.strip():
                return [t / p for p in result.stdout.split() if p.endswith(('.py', '.ts', '.js', '.go', '.java', '.rs'))]
        except Exception:
            pass

    # Full tree scan
    exts = {".py", ".ts", ".js", ".jsx", ".tsx", ".go", ".java", ".rs", ".cpp", ".c", ".h"}
    files = []
    for root, dirs, filenames in os.walk(t):
        dirs[:] = [d for d in dirs if d not in skip]
        for fn in filenames:
            if Path(fn).suffix in exts:
                files.append(Path(root) / fn)
    return files


def main():
    parser = argparse.ArgumentParser(description="DevSquad — 4-Agent Code Review Team")
    parser.add_argument("--target", default=".", help="Target directory")
    parser.add_argument("--focus", choices=["all", "security", "quality", "architecture", "design"], default="all")
    parser.add_argument("--scope", choices=["last-commit", "full"], default="full")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no fixes")
    args = parser.parse_args()

    from pathlib import Path
    import os
    import time

    t0 = time.time()
    files = scan_files(args.target, args.scope)

    report = Report(
        target=args.target,
        focus=args.focus,
        files_reviewed=len(files),
        duration_seconds=0,
    )

    # Placeholder: actual agent delegation happens in the skill invocation layer
    # This script handles scanning and report formatting.
    # The 4-agent fan-out is managed by the skill engine via delegate_task.

    print(f"Scanned {len(files)} files in {args.target}")
    if args.dry_run:
        print("Dry-run mode — no fixes will be applied.")
    print("Run with --help for options.")
    print("\nTo actually run the squad, invoke the skill:")
    print(f'  "dev-squad target={args.target} focus={args.focus} dry_run={args.dry_run}"')


if __name__ == "__main__":
    main()
