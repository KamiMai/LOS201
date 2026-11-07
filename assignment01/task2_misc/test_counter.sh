#!/bin/sh
set -eu
cd /opt/asgn1/task2_misc
insmod ./counter_driver.ko
trap 'rmmod counter_driver' EXIT
cat /proc/counter_info
[ "$(cat /dev/counter)" = 0 ]
[ "$(cat /dev/counter)" = 1 ]
echo 100 > /dev/counter
cat /proc/counter_info
[ "$(cat /dev/counter)" = 100 ]
echo 0 > /dev/counter
cat /proc/counter_info
[ "$(cat /dev/counter)" = 0 ]
if (echo -1 > /dev/counter); then exit 1; fi
if (echo bad > /dev/counter); then exit 1; fi
# One-byte reads must form one snapshot and reach EOF.
echo 123 > /dev/counter
[ "$(dd if=/dev/counter bs=1 2>/dev/null)" = 123 ]
rmmod counter_driver
trap - EXIT
dmesg | grep counter
echo 'TASK2 PASSED'
