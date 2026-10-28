# LAB03 Debugging and performance analysis

Target: Linux 5.15.0, ARMv7 Cortex-A9, QEMU vexpress-a9. Host: Ubuntu x86-64.

This lab adds remote application debugging with GDB, memory analysis with Valgrind, syscall and CPU profiling, and host scheduling latency measurements.

## Progress

- [x] Record the initial host environment.
- [x] Prepare ARM tools and boot the debugging rootfs.
- [x] Capture remote GDB evidence for three application bugs.
- [x] Capture Valgrind results before and after fixes.
- [x] Observe ARM process memory while the process is alive.
- [x] Collect host and ARM strace results and host perf profiles.
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

## Valgrind baseline

The original `leaky_app.c` is unchanged from the assignment. Memcheck reported 16900 bytes definitely lost in 250 blocks: 2100 bytes of names, 2000 bytes of scores and 12800 bytes of message buffers. Indirectly lost was zero. The intentional failing run returned the configured exit code 99. See `logs/valgrind_report.txt`, `logs/valgrind_run.txt` and `logs/leaky_app_output.txt`.

## Memory fixes and ARM observation

The fixed program frees `name` and `scores` before freeing each record, releases message buffers after use, and cleans up partial allocation failures. Memcheck recorded 352 allocations, 352 frees, zero bytes at exit and zero errors.

`memory_observe_arm leaky|fixed` repeats the assignment workload with explicit 5-second and 8-second observation windows. Run `/usr/bin/observe_memory.sh` in QEMU. In this small-workload run, both modes showed VmSize=624 kB, VmRSS=4 kB and VmData=152 kB before and after. These coarse process counters did not expose the 16900-byte leak; Memcheck is the direct evidence. Freeing memory need not return its arena to the OS. See `logs/arm_memory.txt`.

## Profiling results

The measured workload keeps the original math function, consumes search results and varies each query to prevent loop-invariant hoisting. An optional integer argument selects 1-10000 compute iterations; default is 50. `perf_target_original.c` retains the assignment version.

Use `bash embedded_lab3/scripts/profile-host.sh` for host timing/strace and `sudo bash embedded_lab3/scripts/measure-host.sh` for perf and scheduling latency. Perf uses 2000 compute iterations and samples `cycles:u` at 997 Hz; timing/strace and ARM comparison use 50 iterations. Do not compare the two iteration counts as equal workloads.

Final record/report/script/stat completed successfully on perf 7.0.14. The dominant symbols are libm log and heavy_compute, with linear_search now also sampled. The earlier apparent perf failures were target-program crashes: unchecked fopen of a shared /tmp filename failed under sudo with fs.protected_regular=2. The measured program now uses mkstemp and checks I/O. Original failure transcripts are retained.

Rootfs includes memory and profiling apps. The ARM program was checked after the final source change; checksum is 99991021. Gnuplot and FlameGraph outputs are based on the saved raw captures; FlameGraph's upstream commit is recorded.
