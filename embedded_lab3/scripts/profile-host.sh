#!/usr/bin/env bash
set -euo pipefail
lab=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
make -C "$lab/apps" perf_target
/usr/bin/time -v "$lab/apps/perf_target" 50 > "$lab/logs/perf_target_host_output.txt" 2> "$lab/logs/time_host.txt"
strace -o "$lab/logs/strace_full.txt" "$lab/apps/perf_target" 50 > "$lab/logs/strace_app_output.txt" 2>&1
strace -c -o "$lab/logs/strace_summary.txt" "$lab/apps/perf_target" 50
