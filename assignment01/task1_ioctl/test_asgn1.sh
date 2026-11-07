#!/bin/sh
set -eu
cd /opt/asgn1/task1_ioctl
insmod ./asgn1_driver.ko
trap 'rmmod asgn1_driver' EXIT
[ -c /dev/asgn1 ] || mknod /dev/asgn1 c 241 0
./ioctl_test
cat /proc/asgn1_info
rmmod asgn1_driver
trap - EXIT
dmesg | grep asgn1
echo 'TASK1 PASSED'
