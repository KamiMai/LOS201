#!/usr/bin/env bash
set -euo pipefail
lab=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
gdb-multiarch -q -batch \
  -ex "set sysroot $lab/rootfs/initramfs" \
  -directory "$lab/apps" \
  -x "$lab/scripts/debug.gdb" "$lab/apps/buggy_app" \
  2>&1 | tee "$lab/logs/gdb_session.txt"
