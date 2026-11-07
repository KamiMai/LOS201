#!/bin/bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
: "${KERNEL_TARBALL:=$HOME/embedded_lab1/kernel/linux-5.15.tar.xz}"
: "${KERNEL_BUILD_DIR:=$repo/../../work/assignments-kernel}"
if [ ! -d "$KERNEL_BUILD_DIR/linux-5.15" ]; then
    mkdir -p "$KERNEL_BUILD_DIR"
    tar -xJf "$KERNEL_TARBALL" -C "$KERNEL_BUILD_DIR"
fi
kernel=$(cd "$KERNEL_BUILD_DIR/linux-5.15" && pwd)
cp "$repo/assignment_support/kernel/kernel.config" "$kernel/.config"
make -C "$kernel" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- olddefconfig
make -C "$kernel" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- KCFLAGS=-march=armv7-a -j4 zImage dtbs modules
KDIR="$kernel" bash "$repo/assignment_support/scripts/build.sh"
