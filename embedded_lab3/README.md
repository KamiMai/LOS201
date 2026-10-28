# LAB03 Debugging and performance analysis

Target: Linux 5.15.0, ARMv7 Cortex-A9, QEMU vexpress-a9. Host: Ubuntu x86-64.

This lab adds remote application debugging with GDB, memory analysis with Valgrind, syscall and CPU profiling, and host scheduling latency measurements.

## Progress

- [x] Record the initial host environment.
- [x] Prepare ARM tools and boot the debugging rootfs.
- [x] Capture remote GDB evidence for three application bugs.
- [ ] Capture Valgrind results before and after fixes.
- [ ] Observe ARM process memory while the process is alive.
- [ ] Collect host and ARM strace results and host perf profiles.
- [ ] Measure host latency at idle and under load and plot histograms.
- [ ] Complete the report and submission archive.

The real-time section follows D.5: measurements use the current host kernel; PREEMPT_RT is compared theoretically. No RT kernel installation or reboot is required. Recorded maxima are observed results, not guaranteed worst-case bounds.

## Layout

`apps/` holds original and fixed sources and binaries; `scripts/` holds reproducible commands; `logs/` holds actual tool output; `output/` holds the bootable initramfs; `report/` holds the final report.

Device nodes, pseudo-filesystems and downloaded build trees are not tracked. Build outputs required by the assignment are retained. Original LAB01 and LAB02 files are unchanged.

## ARM rootfs

`gdbserver` 15.1 and `strace` 6.8 are Ubuntu armhf packages, downloaded from ports.ubuntu.com. The libc, loader, libstdc++ and libgcc runtime files come from `/usr/arm-linux-gnueabihf/lib`. Applications are linked statically for this lab.

Build the initial app with `make -C embedded_lab3/apps buggy_app`, pack with `bash embedded_lab3/scripts/pack.sh`, then boot with `bash embedded_lab3/scripts/run-qemu.sh`. The packer uses the LAB01 kernel's `usr/gen_init_cpio` helper to create console device nodes without root privileges.

The guest receives 10.0.2.15 through DHCP. Host localhost TCP 1234 is forwarded to guest TCP 1234. Run `gdbserver 0.0.0.0:1234 /usr/bin/buggy_app` in the guest and connect using `gdb-multiarch embedded_lab3/apps/buggy_app` on the host.

Logs retain boot warnings from the inherited kernel; successful module loading, DHCP and application/tool execution must be checked separately.

The minimal rootfs lacks resolver configuration; bind gdbserver explicitly to `0.0.0.0:1234`. The shorthand `:1234` failed name resolution in this image.

## GDB results

Run `bash embedded_lab3/scripts/debug.sh` after starting gdbserver in the guest. The command file captures an out-of-bounds access (`i == len == 5`), a software watchpoint, the same buffer address before/after free, and signed integer overflow. The observed 32-bit product was 1410065408 instead of 10000000000. This buggy run exited normally: absence of a crash does not imply memory safety. Full commands and values are in `logs/gdb_session.txt`.
