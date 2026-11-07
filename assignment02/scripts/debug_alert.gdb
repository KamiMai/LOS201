set pagination off
set confirm off
set debuginfod enabled off
break detect_alert
run --simulate --other -d 3 -i 100 --log /tmp/se205068-gdb-sms.log
info threads
thread apply all bt
set scheduler-locking on
print sample
set variable sample.temperature = 45.0
print sample
next
next
next
print temperature
set scheduler-locking off
disable 1
continue
quit
