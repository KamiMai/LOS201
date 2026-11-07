#!/bin/bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
n=${1:-1}
case "$n" in 1|2) ;; *) echo 'Use 1 or 2' >&2; exit 2;; esac
exec qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -m 512M -smp 2 -nographic \
 -kernel "$repo/assignment_support/kernel/zImage" \
 -dtb "$repo/assignment_support/kernel/vexpress-v2p-ca9.dtb" \
 -initrd "$repo/assignment0$n/output/initramfs_asgn$n.cpio.gz" \
 -append 'console=ttyAMA0,115200 rdinit=/sbin/init mem=512M' \
 -net nic -net user,hostfwd=tcp:127.0.0.1:1234-:1234
