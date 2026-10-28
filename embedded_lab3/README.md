# LAB03 Debugging and performance analysis

Target: Linux 5.15.0, ARMv7 Cortex-A9, QEMU vexpress-a9. Host: Ubuntu x86-64.

This lab adds remote application debugging with GDB, memory analysis with Valgrind, syscall and CPU profiling, and host scheduling latency measurements.

## Progress

- [x] Record the initial host environment.
- [ ] Prepare ARM tools and boot the debugging rootfs.
- [ ] Capture remote GDB evidence for three application bugs.
- [ ] Capture Valgrind results before and after fixes.
- [ ] Observe ARM process memory while the process is alive.
- [ ] Collect host and ARM strace results and host perf profiles.
- [ ] Measure host latency at idle and under load and plot histograms.
- [ ] Complete the report and submission archive.

The real-time section follows D.5: measurements use the current host kernel; PREEMPT_RT is compared theoretically. No RT kernel installation or reboot is required. Recorded maxima are observed results, not guaranteed worst-case bounds.

## Layout

`apps/` holds original and fixed sources and binaries; `scripts/` holds reproducible commands; `logs/` holds actual tool output; `output/` holds the bootable initramfs; `report/` holds the final report.

Device nodes, pseudo-filesystems and downloaded build trees are not tracked. Build outputs required by the assignment are retained. Original LAB01 and LAB02 files are unchanged.
