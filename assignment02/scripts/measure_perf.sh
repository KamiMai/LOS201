#!/bin/bash
set -euo pipefail
lab=$(cd "$(dirname "$0")/.." && pwd)
cd "$lab/logs"
perf_bin=/usr/lib/linux-tools/$(uname -r)/perf
[[ -x "$perf_bin" ]] || perf_bin=$(command -v perf)
sudo "$perf_bin" record -o perf_sms.data -e cpu-clock -F 997 -g -- runuser -u "$(id -un)" -- "$lab/app/sms_app_x86" --simulate --other -i 10 -d 30 --log "$PWD/host_perf_sms.log"
sudo "$perf_bin" report --stdio --no-children -i perf_sms.data > perf_sms.txt
