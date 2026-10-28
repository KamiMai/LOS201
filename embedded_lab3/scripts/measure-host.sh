#!/usr/bin/env bash
set -euo pipefail
ulimit -c 0
[[ $EUID -eq 0 ]] || { echo 'Run with sudo to access perf and SCHED_FIFO.' >&2; exit 1; }
lab=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
logs="$lab/logs"
mkdir -p "$logs"
perf_bin=${PERF_BIN:-perf}
finish() {
    if [[ -n ${stress_pid:-} ]]; then kill "$stress_pid" 2>/dev/null || true; fi
    if [[ -n ${SUDO_UID:-} ]]; then chown "$SUDO_UID:$SUDO_GID" "$logs"/*; fi
}
trap finish EXIT
exec > >(tee "$logs/privileged_measurements.txt") 2>&1
printf 'Started: '; date -Is
uname -a
"$perf_bin" --version
cyclictest --help 2>&1 | head -1 || true
printf 'perf_event_paranoid='; cat /proc/sys/kernel/perf_event_paranoid
printf '\n=== PERF RECORD ===\n'
collect_perf() {
event='cycles:u'
if ! "$perf_bin" record -B -N -e "$event" -F 997 -g -o "$logs/perf.data" -- "$lab/apps/perf_target" 2000 > "$logs/perf_record.txt" 2>&1; then
    cp "$logs/perf_record.txt" "$logs/perf_hardware_unavailable.txt"
    event='cpu-clock:u'
    "$perf_bin" record -B -N -e "$event" -F 997 -g -o "$logs/perf.data" -- "$lab/apps/perf_target" 2000 > "$logs/perf_record.txt" 2>&1 || return 1
fi
printf 'Sampling event: %s\nIterations: 2000\nFrequency: 997 Hz\nBuild-id collection/cache disabled\n' "$event" > "$logs/perf_method.txt"
"$perf_bin" report -f --stdio --no-children --percent-limit 0 -i "$logs/perf.data" > "$logs/perf_report.txt" || return 1
if ! "$perf_bin" stat -e task-clock,context-switches,cpu-migrations,page-faults,cycles,instructions,cache-misses,branches,branch-misses -- "$lab/apps/perf_target" 2000 > "$logs/perf_stat_app.txt" 2> "$logs/perf_stat.txt"; then
    cp "$logs/perf_stat.txt" "$logs/perf_stat_hardware_unavailable.txt"
    "$perf_bin" stat -e task-clock,context-switches,page-faults -- "$lab/apps/perf_target" 2000 > "$logs/perf_stat_app.txt" 2> "$logs/perf_stat.txt" || return 1
fi
"$perf_bin" script -f -i "$logs/perf.data" > "$logs/perf_stacks.txt" || return 1
}
if collect_perf; then
    echo 'Perf collection completed.'
    rm -f "$logs/perf.failed"
else
    echo 'Perf collection failed; see logs. Continuing with latency.'
    touch "$logs/perf.failed"
fi

common=(--mlockall --threads=4 --affinity=0-3 --policy=fifo --priority=80 --interval=1000 --distance=0 --duration=60s --histogram=10000 --quiet)
echo 'Settling for 15 seconds before latency measurements.'
sleep 15
printf '\n=== IDLE LATENCY ===\n'
date -Is
cyclictest "${common[@]}" --histfile="$logs/hist_standard.txt" --json="$logs/cyclic_idle.json" > "$logs/cyclic_idle.txt" 2>&1
printf '\n=== LOADED LATENCY ===\n'
stress-ng --cpu "$(nproc)" --io 2 --vm 2 --vm-bytes 256M --timeout 70s > "$logs/stress_ng.txt" 2>&1 &
stress_pid=$!
sleep 5
date -Is
cyclictest "${common[@]}" --histfile="$logs/hist_loaded.txt" --json="$logs/cyclic_loaded.json" > "$logs/cyclic_loaded.txt" 2>&1
wait "$stress_pid"
unset stress_pid
printf '\nCompleted: '; date -Is
printf 'No sysctl or kernel changes were made.\n'
touch "$logs/measurements.complete"
