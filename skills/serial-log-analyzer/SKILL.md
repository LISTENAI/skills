---
name: serial-log-analyzer
description: Capture and analyze serial port logs from embedded devices (via picocom, minicom, screen, or ttylog) to detect errors, warnings, and anomalies. Use when the user mentions "串口日志", "serial log", "picocom", "minicom", "设备日志", "固件日志", "嵌入式日志", "log analysis", "error trace", or needs to diagnose firmware/embedded system issues from serial output. Analyzes log patterns, maps them back to source code locations, and provides root cause suggestions.
license: MIT
---

# Serial Log Analyzer

Capture serial port logs from embedded devices and use AI to detect anomalies, map log lines to source code, and diagnose firmware issues.

## Quick Reference

| Task | Reference |
|------|-----------|
| Capture logs | [capture-tools.md](references/capture-tools.md) |
| Log patterns & severity | [log-patterns.md](references/log-patterns.md) |
| Analyze log file | Run `scripts/analyze_log.py` |

## Workflow

### 1. Capture Serial Log

See [capture-tools.md](references/capture-tools.md) for picocom, minicom, screen, ttylog usage.

Quick capture with picocom:
```bash
picocom -b 115200 /dev/ttyUSB0 | tee /tmp/serial.log
# Ctrl+A, Ctrl+X to exit
```

### 2. Analyze Log

Run the analysis script on the captured log:
```bash
python3 scripts/analyze_log.py /tmp/serial.log
```

Or pass log content directly for AI analysis — paste the log and ask:
> "分析这段串口日志，找出错误和警告"

### 3. Map to Source Code

When errors are found, locate source code to cross-reference:

1. Extract the log tag/module name (e.g., `[BT]`, `[AUDIO]`, `[MEM]`)
2. Search codebase: `grep -r "LOG_TAG\|TAG.*=.*\"<module>\"" src/`
3. Find the exact log call: `grep -rn "error message substring" src/`
4. Read surrounding context (±20 lines) to understand conditions

### 4. Diagnose & Report

Provide structured analysis:
- **Severity summary**: counts of ERROR / WARN / INFO
- **Error details**: timestamp, module, message, frequency
- **Source location**: file:line where log is emitted
- **Root cause hypothesis**: based on log sequence and code context
- **Suggested fix**: concrete next steps

## Log Format Conventions (CSK/LISA firmware)

Most LISTENAI firmware uses structured logs:
```
[timestamp][LEVEL][MODULE] message
```

Common patterns:
- `[E]` / `ERROR` / `error:` → critical issues
- `[W]` / `WARN` / `warning:` → non-fatal but needs attention
- `assert` / `panic` / `fault` / `HardFault` → system crash
- `heap` / `malloc` / `alloc` → memory issues
- `timeout` / `retry` → communication issues

See [log-patterns.md](references/log-patterns.md) for complete pattern reference.
