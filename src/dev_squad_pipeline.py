#!/usr/bin/env python3
"""
DevSquad — Standalone LangGraph Multi-Agent Code Review Pipeline

Architecture:
  start → scan → [architect, quality, security, design] → aggregate → finalize → end

Usage:
  python dev_squad_pipeline.py --target . --focus all
  python dev_squad_pipeline.py --target src/ --focus security --dry-run
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any
from enum import Enum
from datetime import datetime


# ──────────────────────────────────────────────────
# Data Types
# ──────────────────────────────────────────────────

class RiskTier(str, Enum):
    SAFE = "SAFE"
    CAREFUL = "CAREFUL"
    RISKY = "RISKY"
    BUG = "BUG"


@dataclass
class Finding:
    file: str
    line: int | None
    tier: str
    category: str
    description: str
    suggested_fix: str
    confidence: float
    risk_desc: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class SquadState:
    target: str
    focus: str
    files: list[str]
    findings: list[Finding] = field(default_factory=list)
    duration: float = 0.0
    started_at: str = ""

    def to_dict(self):
        return {
            "target": self.target,
            "focus": self.focus,
            "files": self.files,
            "findings": [f.to_dict() for f in self.findings],
            "duration": self.duration,
            "started_at": self.started_at,
        }


# ──────────────────────────────────────────────────
# Scanning
# ──────────────────────────────────────────────────

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".tox", ".hg"}
SOURCE_EXTS = {".py", ".ts", ".js", ".jsx", ".tsx", ".go", ".java", ".rs", ".cpp", ".c", ".h"}


def scan_files(target: str, scope: str = "full") -> list[str]:
    """Collect source files for review."""
    t = Path(target).resolve()
    if not t.exists():
        raise FileNotFoundError(f"Target not found: {target}")

    if scope == "last-commit":
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True, text=True, cwd=t
            )
            if result.returncode == 0 and result.stdout.strip():
                changed = [p for p in result.stdout.split() if Path(p).suffix in SOURCE_EXTS]
                if changed:
                    return [str(t / p) for p in changed]
        except Exception as e:
            print(f"[scan] git diff failed: {e}", file=sys.stderr)

    files = []
    for root, dirs, filenames in os.walk(t):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in filenames:
            if Path(fn).suffix in SOURCE_EXTS:
                files.append(str(Path(root) / fn))
    return sorted(files)


# ──────────────────────────────────────────────────
# Reviewer Functions (simulated — replace with real LLM calls)
# ──────────────────────────────────────────────────

async def review_architecture(state: SquadState) -> dict:
    """Agent 1: System design & architectural patterns."""
    findings = []
    # Placeholder: in production, this calls an LLM with the codebase context
    # to detect architecture violations, coupling issues, missing abstractions.
    return {"findings": findings}


async def review_quality(state: SquadState) -> dict:
    """Agent 2: Code quality, duplication, complexity."""
    findings = []
    return {"findings": findings}


async def review_security(state: SquadState) -> dict:
    """Agent 3: OWASP, secrets, injection, auth gaps."""
    findings = []
    # Light static check for obvious issues
    import re
    SECRET_PATTERNS = [
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'Potential hardcoded API key'),
        (r'password\s*=\s*["\'][^"\']+["\']', 'Potential hardcoded password'),
        (r'print\(.*password', 'Password logged'),
    ]
    for fpath in state.files:
        try:
            content = Path(fpath).read_text(errors='ignore')
            for pattern, desc in SECRET_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    findings.append(Finding(
                        file=fpath,
                        line=None,
                        tier=RiskTier.BUG.value,
                        category="security",
                        description=desc,
                        suggested_fix="Move to environment variable",
                        confidence=0.9,
                    ))
        except Exception:
            pass
    return {"findings": findings}


async def review_design(state: SquadState) -> dict:
    """Agent 4: UI/UX consistency, API design, naming."""
    findings = []
    return {"findings": findings}


# ──────────────────────────────────────────────────
# Graph Nodes
# ──────────────────────────────────────────────────

async def node_scan(state: SquadState) -> SquadState:
    """Step 1: Scan files."""
    state.files = scan_files(state.target, scope="last-commit")
    state.started_at = datetime.now().isoformat()
    return state


async def node_review(state: SquadState) -> SquadState:
    """Step 2: Fan out 4 reviewers in parallel."""
    tasks = [
        review_architecture(state),
        review_quality(state),
        review_security(state),
        review_design(state),
    ]
    results = await asyncio.gather(*tasks)
    for r in results:
        state.findings.extend(r["findings"])
    return state


async def node_aggregate(state: SquadState) -> SquadState:
    """Step 3: Deduplicate and tier findings."""
    seen = set()
    unique = []
    for f in state.findings:
        key = (f.file, f.line, f.category, f.description[:50])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    state.findings = sorted(unique, key=lambda x: ({"BUG": 0, "RISKY": 1, "CAREFUL": 2, "SAFE": 3}[x.tier], x.file))
    return state


async def node_finalize(state: SquadState) -> SquadState:
    """Step 4: Calculate duration and format output."""
    state.duration = time.time() - state._start_time if hasattr(state, '_start_time') else 0.0
    return state


# ──────────────────────────────────────────────────
# Pipeline Runner
# ──────────────────────────────────────────────────

class DevSquadPipeline:
    def __init__(self, target: str, focus: str = "all", dry_run: bool = False):
        self.target = target
        self.focus = focus
        self.dry_run = dry_run
        self.state = SquadState(target=target, focus=focus, files=[], started_at="")
        self.state._start_time = time.time()

    async def run(self) -> SquadState:
        """Execute the 4-agent pipeline."""
        self.state = await node_scan(self.state)
        self.state = await node_review(self.state)
        self.state = await node_aggregate(self.state)
        self.state = await node_finalize(self.state)
        return self.state

    def print_report(self):
        """Print formatted report."""
        report = self.state
        safe = [f for f in report.findings if f.tier == RiskTier.SAFE.value]
        careful = [f for f in report.findings if f.tier == RiskTier.CAREFUL.value]
        risky = [f for f in report.findings if f.tier == RiskTier.RISKY.value]
        bugs = [f for f in report.findings if f.tier == RiskTier.BUG.value]

        w = min(72, max(60, len(report.target) + 10))
        sep = "═" * w
        print(f"\n{sep}")
        print(f"  DEV SQUAD REPORT — {report.target}")
        print(f"  Focus: {report.focus} | Files reviewed: {len(report.files)}")
        print(f"  Duration: {report.duration:.1f}s | Findings: {len(report.findings)}")
        print(sep)

        if bugs:
            print(f"\n⚠️  BUGS — {len(bugs)} issue(s)\n")
            for f in bugs[:10]:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                print(f"  [{loc}] {f.description}")
                print(f"    Fix: {f.suggested_fix}")

        if safe:
            print(f"\n🟢 SAFE — Auto-applicable ({len(safe)})\n")
            for f in safe[:5]:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                print(f"  [{loc}] {f.description}")

        if careful:
            print(f"\n🟡 CAREFUL — Apply with verification ({len(careful)})\n")
            for f in careful[:5]:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                print(f"  [{loc}] {f.description}")

        if risky:
            print(f"\n🔴 RISKY — Needs human review ({len(risky)})\n")
            for f in risky[:5]:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                print(f"  [{loc}] {f.description}")
                print(f"    {f.risk_desc or f.suggested_fix}")

        if not report.findings:
            print("\n✅ No issues found.")

        if self.dry_run:
            print("\n[Dry-run mode — no fixes applied]")


# ──────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import subprocess

    parser = argparse.ArgumentParser(description="DevSquad — 4-Agent Code Review Pipeline")
    parser.add_argument("--target", default=".", help="Target directory")
    parser.add_argument("--focus", choices=["all", "security", "quality", "architecture", "design"], default="all")
    parser.add_argument("--scope", choices=["last-commit", "full"], default="full")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no fixes")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    pipeline = DevSquadPipeline(target=args.target, focus=args.focus, dry_run=args.dry_run)
    state = asyncio.run(pipeline.run())

    if args.json:
        print(json.dumps(state.to_dict(), indent=2))
    else:
        pipeline.print_report()
