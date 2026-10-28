#!/bin/sh
set -eu
for mode in leaky fixed; do
    memory_observe_arm "$mode" &
    pid=$!
    sleep 1
    echo "=== MODE=$mode BEFORE PID=$pid ==="
    grep -E 'VmRSS|VmSize|VmData' /proc/$pid/status
    cat /proc/$pid/maps
    sleep 5
    echo "=== MODE=$mode AFTER PID=$pid ==="
    grep -E 'VmRSS|VmSize|VmData' /proc/$pid/status
    cat /proc/$pid/maps
    wait "$pid"
done
