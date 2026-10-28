#!/usr/bin/env bash
set -u
ulimit -c 0
[[ $EUID -eq 0 ]] || { echo 'Run with sudo.' >&2; exit 1; }
lab=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
logs="$lab/logs"
perf_bin=${PERF_BIN:-perf}
trap 'if [[ -n ${SUDO_UID:-} ]]; then chown "$SUDO_UID:$SUDO_GID" "$logs"/*; fi' EXIT
exec > >(tee "$logs/perf_recovery.txt") 2>&1
date -Is
"$perf_bin" --version
if [[ -f "$logs/perf.data" ]]; then mv "$logs/perf.data" "$logs/perf_failed_capture.data"; fi
"$perf_bin" record -B -N -e cycles:u -F 99 -g -o "$logs/perf.data" -- "$lab/apps/perf_target" 2000 > "$logs/perf_record.txt" 2>&1
status=$?
printf 'record_exit_status=%s\n' "$status"
printf 'Sampling event: cycles:u\nFrequency: 99 Hz\nIterations: 2000\nBuild-id collection/cache disabled (-B -N)\nRecord exit status: %s\n' "$status" > "$logs/perf_method.txt"
if [[ $status -ne 0 ]]; then
    gdb -q -batch -ex run -ex 'thread apply all bt' --args "$perf_bin" record -B -N -e cpu-clock:u -F 99 -g -o "$logs/perf_debug.data" -- "$lab/apps/perf_target" 2000 > "$logs/perf_tool_backtrace.txt" 2>&1
fi
"$perf_bin" report -f --stdio --no-children --percent-limit 0 -i "$logs/perf.data" > "$logs/perf_report.txt" 2> "$logs/perf_report_errors.txt"
report_status=$?
"$perf_bin" script -f -i "$logs/perf.data" > "$logs/perf_stacks.txt" 2> "$logs/perf_script_errors.txt"
script_status=$?
"$perf_bin" stat -e task-clock,context-switches,cpu-migrations,page-faults,cycles,instructions,cache-misses,branches,branch-misses -- "$lab/apps/perf_target" 2000 > "$logs/perf_stat_app.txt" 2> "$logs/perf_stat.txt"
stat_status=$?
printf 'report_exit_status=%s script_exit_status=%s stat_exit_status=%s\n' "$report_status" "$script_status" "$stat_status"
if [[ $status -eq 0 && $report_status -eq 0 && $script_status -eq 0 && $stat_status -eq 0 ]]; then
    rm -f "$logs/perf.failed"
    touch "$logs/perf.complete"
else
    echo 'One or more perf commands failed; preserve logs and inspect before reporting success.'
    exit 1
fi
