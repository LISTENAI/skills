#!/usr/bin/env python3
"""
Serial log analyzer — detect errors, warnings, and anomalies.
Usage: python3 analyze_log.py <log_file> [--json]
"""

import re
import sys
import json
import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional

PATTERNS = {
    "CRITICAL": [
        r"HardFault", r"UsageFault", r"BusFault", r"MemManage",
        r"\bpanic\b", r"\bassert\b", r"\babort\b", r"\bFATAL\b",
        r"stack overflow", r"watchdog", r"reset reason",
    ],
    "ERROR": [
        r"\[E\]", r"\bERROR\b", r"\berror:\s", r"\bERR\b",
        r"\bfailed\b", r"\bFAILED\b", r"init fail", r"load fail",
        r"alloc fail", r"malloc fail", r"out of memory",
        r"CRC error", r"timeout", r"NACK", r"\bNAK\b",
    ],
    "WARNING": [
        r"\[W\]", r"\bWARN\b", r"\bwarning:\s", r"\bdeprecated\b",
        r"retry", r"queue full", r"overflow", r"underrun", r"overrun",
    ],
}

MODULE_RE = re.compile(r"\[([A-Z_][A-Z0-9_]{1,15})\]")
TIMESTAMP_RE = re.compile(r"^\[?(\d{2}:\d{2}:\d{2}[\.,]\d{0,6}|\d+\.\d+|\d+)\]?\s*")


@dataclass
class LogEntry:
    line_no: int
    raw: str
    severity: str
    module: Optional[str]
    timestamp: Optional[str]


def detect_severity(line: str) -> str:
    for level in ("CRITICAL", "ERROR", "WARNING"):
        for pat in PATTERNS[level]:
            if re.search(pat, line, re.IGNORECASE):
                return level
    return "INFO"


def parse_log(lines: List[str]) -> List[LogEntry]:
    entries = []
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if not line:
            continue
        severity = detect_severity(line)
        module_m = MODULE_RE.search(line)
        module = module_m.group(1) if module_m else None
        ts_m = TIMESTAMP_RE.match(line)
        timestamp = ts_m.group(1) if ts_m else None
        entries.append(LogEntry(i, line, severity, module, timestamp))
    return entries


def summarize(entries: List[LogEntry]) -> dict:
    counts = defaultdict(int)
    by_module: dict = defaultdict(lambda: defaultdict(list))
    anomalies: List[dict] = []

    for e in entries:
        counts[e.severity] += 1
        if e.severity in ("CRITICAL", "ERROR", "WARNING"):
            by_module[e.module or "UNKNOWN"][e.severity].append(e)
            anomalies.append({
                "line": e.line_no,
                "severity": e.severity,
                "module": e.module,
                "message": e.raw.strip(),
            })

    return {
        "total_lines": len(entries),
        "counts": dict(counts),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "modules": {
            mod: {lvl: len(lst) for lvl, lst in lvls.items()}
            for mod, lvls in by_module.items()
        },
    }


def print_report(result: dict) -> None:
    c = result["counts"]
    print("=" * 60)
    print("Serial Log Analysis Report")
    print("=" * 60)
    print(f"Total lines : {result['total_lines']}")
    print(f"CRITICAL    : {c.get('CRITICAL', 0)}")
    print(f"ERROR       : {c.get('ERROR', 0)}")
    print(f"WARNING     : {c.get('WARNING', 0)}")
    print(f"INFO        : {c.get('INFO', 0)}")
    print()

    if result["anomaly_count"] == 0:
        print("✅ No errors or warnings detected.")
        return

    print(f"⚠️  {result['anomaly_count']} anomalies found:\n")

    # Group by severity
    for sev in ("CRITICAL", "ERROR", "WARNING"):
        items = [a for a in result["anomalies"] if a["severity"] == sev]
        if not items:
            continue
        icon = {"CRITICAL": "🔴", "ERROR": "🟠", "WARNING": "🟡"}[sev]
        print(f"{icon} {sev} ({len(items)})")
        for a in items[:20]:  # cap output
            mod = f"[{a['module']}] " if a['module'] else ""
            print(f"  L{a['line']:>5}: {mod}{a['message'][:100]}")
        if len(items) > 20:
            print(f"  ... and {len(items) - 20} more")
        print()

    # Module summary
    if result["modules"]:
        print("Module breakdown:")
        for mod, lvls in sorted(result["modules"].items()):
            parts = ", ".join(f"{l}={n}" for l, n in lvls.items())
            print(f"  {mod:20s} {parts}")


def main():
    parser = argparse.ArgumentParser(description="Analyze serial log for anomalies")
    parser.add_argument("log_file", help="Path to serial log file")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    try:
        with open(args.log_file, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: file not found: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    entries = parse_log(lines)
    result = summarize(entries)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report(result)


if __name__ == "__main__":
    main()
