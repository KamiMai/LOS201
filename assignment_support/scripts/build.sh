#!/bin/bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
: "${KDIR:?Set KDIR to the configured, built ARM Linux 5.15 tree}"
make -C "$repo/assignment01/task1_ioctl" KDIR="$KDIR" KCFLAGS=-march=armv7-a
make -C "$repo/assignment01/task2_misc" KDIR="$KDIR" KCFLAGS=-march=armv7-a
make -C "$repo/assignment02/driver" KDIR="$KDIR"
make -C "$repo/assignment02/app" host arm
cp "$KDIR/arch/arm/boot/zImage" "$repo/assignment_support/kernel/"
cp "$KDIR/arch/arm/boot/dts/vexpress-v2p-ca9.dtb" "$repo/assignment_support/kernel/"
cp "$KDIR/.config" "$repo/assignment_support/kernel/kernel.config"
GEN_INIT_CPIO="$KDIR/usr/gen_init_cpio" python3 "$repo/assignment_support/scripts/pack.py" 1
GEN_INIT_CPIO="$KDIR/usr/gen_init_cpio" python3 "$repo/assignment_support/scripts/pack.py" 2
