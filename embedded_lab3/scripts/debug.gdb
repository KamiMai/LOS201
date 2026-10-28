set pagination off
set confirm off
set print pretty on
set debuginfod enabled off
set architecture arm
set remotetimeout 20
target remote 127.0.0.1:1234
break main
continue
next
next
next
print arr
info registers pc sp lr
break buggy_app.c:9 if i == len
continue
echo \n=== ARRAY OUT OF BOUNDS ===\n
print i
print len
print data[0]@5
print data + len
set can-use-hw-watchpoints 0
watch i
next
next
backtrace
info registers pc sp lr
delete breakpoints
break buggy_app.c:18
continue
echo \n=== BEFORE FREE ===\n
print buf
set $saved_buf = buf
x/s $saved_buf
next
echo \n=== AFTER FREE ===\n
print buf
x/s $saved_buf
backtrace
delete breakpoints
break calculate
continue
echo \n=== INTEGER OVERFLOW ===\n
print a
print b
print (long long)a * (long long)b
next
print result
info registers
backtrace
delete breakpoints
continue
quit
