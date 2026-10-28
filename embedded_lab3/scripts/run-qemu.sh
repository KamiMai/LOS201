#!/usr/bin/env bash
set -euo pipefail
lab=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
repo=$(dirname -- "$lab")
exec qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -m 512M -smp 2 -nographic \
  -kernel "$repo/embedded_lab1/output/zImage" \
  -dtb "$repo/embedded_lab1/output/vexpress-v2p-ca9.dtb" \
  -initrd "$lab/output/initramfs_lab3.cpio.gz" \
  -append 'console=ttyAMA0,115200 rdinit=/sbin/init mem=512M' \
  -net nic -net user,hostfwd=tcp:127.0.0.1:1234-:1234
