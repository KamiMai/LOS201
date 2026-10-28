#!/usr/bin/env bash
set -euo pipefail
lab=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
repo=$(dirname -- "$lab")
lab1_output=${LAB1_OUTPUT:-$repo/embedded_lab1/output}
if [[ ! -f "$lab1_output/zImage" && -z ${LAB1_OUTPUT:-} ]]; then
  lab1_output="$HOME/embedded_lab1/output"
fi
[[ -f "$lab1_output/zImage" && -f "$lab1_output/vexpress-v2p-ca9.dtb" ]] || {
  echo 'Set LAB1_OUTPUT to the LAB01 directory containing zImage and the DTB.' >&2
  exit 1
}
exec qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -m 512M -smp 2 -nographic \
  -kernel "$lab1_output/zImage" \
  -dtb "$lab1_output/vexpress-v2p-ca9.dtb" \
  -initrd "$lab/output/initramfs_lab3.cpio.gz" \
  -append 'console=ttyAMA0,115200 rdinit=/sbin/init mem=512M' \
  -net nic -net user,hostfwd=tcp:127.0.0.1:1234-:1234
