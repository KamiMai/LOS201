#!/usr/bin/env bash
set -euo pipefail
lab=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
gen=${GEN_INIT_CPIO:-$HOME/embedded_lab1/kernel/linux-5.15/usr/gen_init_cpio}
[[ -x "$gen" ]] || { echo "Set GEN_INIT_CPIO to the Linux usr/gen_init_cpio executable." >&2; exit 1; }
mkdir -p "$lab/rootfs/initramfs/"{dev,proc,sys,tmp,root} "$lab/output"
manifest=$(mktemp)
trap 'rm -f "$manifest"' EXIT
python3 "$lab/scripts/cpio_manifest.py" "$lab/rootfs/initramfs" > "$manifest"
"$gen" "$manifest" | gzip -9 > "$lab/output/initramfs_lab3.cpio.gz"
gzip -t "$lab/output/initramfs_lab3.cpio.gz"
ls -lh "$lab/output/initramfs_lab3.cpio.gz"
