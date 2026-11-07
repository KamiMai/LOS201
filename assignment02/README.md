# Assignment 02 - Sensor Monitoring System

Mai Thế Tâm - SE205068 - LOS201.

Four worker threads: Sensor, Processor, Alert and Logger. The default backend
uses `/dev/sms_sensor`; `--simulate` selects an explicit HOST-only data generator
for Valgrind/profiling without loading experimental modules into the HOST.
HOST measurements do not measure the ARM kernel driver.

Build with `make -C app host arm`. Default scheduling is FIFO priority 50;
`--other` explicitly selects SCHED_OTHER for comparison.

Implementation and evidence are being added in separate verified milestones.
