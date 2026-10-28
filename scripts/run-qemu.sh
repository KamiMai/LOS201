#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
case "${1:-2}" in
  1) initrd="$repo_dir/embedded_lab1/output/initramfs.cpio.gz" ;;
  2) initrd="$repo_dir/embedded_lab2/output/initramfs_lab2.cpio.gz" ;;
  *) echo "Usage: bash scripts/run-qemu.sh [1|2]" >&2; exit 2 ;;
esac
command -v qemu-system-arm >/dev/null || { echo 'Install qemu-system-arm first.' >&2; exit 1; }
exec qemu-system-arm \
  -M vexpress-a9 -cpu cortex-a9 -m 512M -smp 2 -nographic \
  -kernel "$repo_dir/embedded_lab1/output/zImage" \
  -dtb "$repo_dir/embedded_lab1/output/vexpress-v2p-ca9.dtb" \
  -initrd "$initrd" \
  -append 'console=ttyAMA0,115200 rdinit=/sbin/init mem=512M'
