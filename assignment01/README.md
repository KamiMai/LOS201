# Assignment 01 - How to Write a Device Driver

**Mai Thế Tâm - SE205068 - LOS201**

- `task1_ioctl/`: `/dev/asgn1`, major 241; RESET_BUFFER, GET_STATS,
  SET_MODE, GET_VERSION; shared ABI header and C userspace tester.
- `task2_misc/`: `/dev/counter`, misc major 10, atomic counter, per-open
  partial-read snapshot and `/proc/counter_info`.
- `logs/`: real ARM/QEMU test outputs, including negative tests and dmesg.
- `bao_cao/`: technical report, architecture and theory answers.
- `output/`: bootable image and self-contained submission archive.

From the repository root:

```bash
bash assignment_support/scripts/run-qemu.sh 1
```

Press Enter in QEMU, then run:

```sh
/opt/asgn1/task1_ioctl/test_asgn1.sh
/opt/asgn1/task2_misc/test_counter.sh
```

Both tests passed on Linux 5.15 ARMv7. Expected invalid-argument errors are
asserted negative tests. See `assignment_support/README.md` to rebuild the
kernel/modules. Each Makefile supports `make` and `make clean` with KDIR set
to the matching ARM kernel. The assignment does not replace LAB02 devices.
