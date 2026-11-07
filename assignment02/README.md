# Assignment 02 - Sensor Monitoring System

**Mai Thế Tâm - SE205068 - LOS201**

Four workers implement Sensor -> bounded ring -> Processor -> alarm queue ->
Alert, with a separate log queue and Logger. Default: 500 ms, FIFO priority 50,
60 seconds. Both HOST and ARM builds pass `-Wall -Wextra -Werror`.

## Run on ARM

From the repository root:

```bash
bash assignment_support/scripts/run-qemu.sh 2
```

Press Enter in QEMU:

```sh
test_arm.sh
```

The script loads the sensor module, measures process memory at 5/30/55 s,
logs the 60-second run, and retains results under `/tmp`. To demonstrate
SIGINT independently after the test:

```sh
sms_app -d 0 -v
```

Press Ctrl+C. Close the application before `rmmod sms_sensor_driver`.

## Measurements captured

- ARM 60 s: 118 accepted samples, 118 consumed, zero ring overflow;
  proc read_count changes from 0 to 118 (within the required 120 +/- 10).
- VmSize 4020 KiB / VmRSS 2748 KiB at 5, 30 and 55 seconds.
- ARM jitter, 100 ms interval, 1000 wake-ups per run:
  FIFO P99 2679 us, OTHER P99 3183 us (15.83% lower in this experiment).
  Maxima 5571 / 6085 us exceed an illustrative 5 ms budget; this is not a
  hard real-time guarantee. Driver EAGAIN retries mean wake-ups and accepted
  samples differ; both counts are recorded.
- HOST Valgrind: >=31 s followed by SIGINT, zero bytes left and zero errors.
- HOST GDB alert injection, strace -f -c, CPU time and perf captures included.
  HOST `--simulate` exercises application/IPC only, not the ARM sensor driver.
  perf is the retained pre-padding-fix development snapshot, labeled in report.
- Rotation above 1 MiB and invalid CLI/device tests passed.

## Rebuild and repeat

```bash
make -C app host arm
python3 scripts/measure_host.py
bash scripts/measure_perf.sh
```

Use `scripts/debug_alert.gdb` with GDB on `app/sms_app_x86`. The default backend
uses `/dev/sms_sensor`; `--simulate` is explicit, never a silent fallback.
Additional flags: `--other`, `--samples`, `--device`, `--log`, `--jitter`.
See `../assignment_support/README.md` for the matching kernel and image build.

Video and personal reflection are omitted as requested. The written assignment
rubric requests them, so these portions are not represented as completed.
