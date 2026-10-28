#!/usr/bin/env bash
set -u
printf 'Recorded: '; date -Is
uname -a
printf '\nHost architecture: '; uname -m
printf '\nCompiler\n'; gcc --version | head -1
printf '\nARM compiler\n'; arm-linux-gnueabihf-gcc --version | head -1
printf '\nKernel configuration\n'
grep -E '^CONFIG_(PREEMPT.*|PERF_EVENTS|HIGH_RES_TIMERS)=' "/boot/config-$(uname -r)" || true
printf '\nTools\n'
for tool in qemu-system-arm gdb-multiarch gdbserver valgrind strace perf cyclictest gnuplot stress-ng; do
  if command -v "$tool" >/dev/null 2>&1; then command -v "$tool"; else printf '%s: missing\n' "$tool"; fi
done
printf '\nCPU\n'; lscpu | grep -E 'Architecture:|CPU\(s\):|Model name:|Thread\(s\) per core:|Core\(s\) per socket:'
