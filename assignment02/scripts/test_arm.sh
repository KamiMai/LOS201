#!/bin/sh
set -eu
insmod /lib/modules/5.15.0/sms_sensor_driver.ko
cat /proc/sms_stats > /tmp/proc_sms_stats_before.txt
sms_app -d 60 -i 500 -v --log /tmp/sms.log --jitter /tmp/arm60_jitter.txt > /tmp/sms_sample_run.txt 2>&1 &
pid=$!
sleep 5
cat /proc/$pid/status > /tmp/memory_5.txt
cat /proc/$pid/maps > /tmp/maps.txt
ls /proc/$pid/task > /tmp/thread_ids.txt
sleep 25
cat /proc/$pid/status > /tmp/memory_30.txt
sleep 25
cat /proc/$pid/status > /tmp/memory_55.txt
wait "$pid"
cat /proc/sms_stats > /tmp/proc_sms_stats_after.txt
cat /tmp/sms_sample_run.txt
cat /tmp/arm60_jitter.txt
cat /proc/sms_stats
echo ARM60_PASS
