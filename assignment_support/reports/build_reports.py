#!/usr/bin/env python3
"""Build evidence-based assignment reports. Mai The Tam - SE205068."""
from pathlib import Path
import re, html, json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
repo=Path(__file__).resolve().parents[2]
font=Path('/usr/share/fonts/truetype/dejavu')
for name,file in [('Body','DejaVuSans.ttf'),('Bold','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf')]:
 pdfmetrics.registerFont(TTFont(name,str(font/file)))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Text',fontName='Body',fontSize=12,leading=17,spaceAfter=10))
styles.add(ParagraphStyle(name='Heading',fontName='Bold',fontSize=17,leading=22,spaceAfter=14,textColor=colors.HexColor('#143a59')))
styles.add(ParagraphStyle(name='SmallText',fontName='Body',fontSize=9,leading=13,spaceAfter=7))
styles.add(ParagraphStyle(name='CodeText',fontName='Mono',fontSize=8,leading=11,spaceAfter=10))
styles.add(ParagraphStyle(name='Cover',fontName='Bold',fontSize=25,leading=33,alignment=TA_CENTER,spaceAfter=22))
def text(s):return Paragraph(html.escape(s).replace('\n','<br/>'),styles['Text'])
def code(s):
 # Explicit wrapping prevents terminal lines from spilling beyond margins.
 import textwrap
 lines=[]
 for l in s.splitlines():lines+=textwrap.wrap(l,88,replace_whitespace=False,drop_whitespace=False) or ['']
 return Preformatted('\n'.join(lines),styles['CodeText'])
def table(rows,widths=None):
 cells=[[Paragraph(html.escape(str(c)),styles['SmallText']) for c in row] for row in rows]
 t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eff5')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#b7c7d3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
 return t
def diagram(kind):
 d=Drawing(475,270)
 def box(x,y,w,h,label):
  d.add(Rect(x,y,w,h,rx=5,fillColor=colors.HexColor('#eef4f8'),strokeColor=colors.HexColor('#245477')))
  for i,line in enumerate(label.split('\n')):d.add(String(x+w/2,y+h/2+5-12*i,line,fontName='Body',fontSize=9,textAnchor='middle'))
 def arrow(x1,y1,x2,y2):
  d.add(Line(x1,y1,x2,y2,strokeColor=colors.HexColor('#245477'),strokeWidth=1))
  if y2<y1:d.add(Polygon([x2,y2,x2-3,y2+6,x2+3,y2+6],fillColor=colors.HexColor('#245477')))
  else:d.add(Polygon([x2,y2,x2-6,y2+3,x2-6,y2-3],fillColor=colors.HexColor('#245477')))
 if kind==1:
  box(100,220,275,40,'Userspace: ioctl_test / shell')
  box(100,155,275,40,'read / write / ioctl -> VFS')
  box(0,75,220,50,'asgn1 file_operations\nunlocked_ioctl + buffer + mutex')
  box(255,75,220,50,'counter file_operations\natomic_t + per-open snapshot')
  box(0,0,220,40,'/dev/asgn1 + /proc/asgn1_info')
  box(255,0,220,40,'/dev/counter + /proc/counter_info')
  arrow(237,220,237,195);arrow(160,155,110,125);arrow(310,155,360,125)
  arrow(110,75,110,40);arrow(360,75,360,40)
  d.add(String(110,57,'copy_to/from_user',fontName='Body',fontSize=8,textAnchor='middle'))
 else:
  box(0,220,145,40,'sms_sensor_driver\n/dev + /proc + ioctl')
  box(180,220,125,40,'Sensor Thread\nFIFO 50 / absolute sleep')
  box(350,220,125,40,'Circular buffer\nmutex + condition')
  box(350,125,125,50,'Processor Thread\nwindow of 10')
  box(180,125,125,50,'alarm_queue\nPOSIX mq')
  box(0,125,135,50,'Alert Thread\n3 alarm counters')
  box(130,20,170,50,'log_queue -> Logger\nflush + rotation')
  box(345,20,130,50,'/tmp/sms.log')
  arrow(145,240,180,240);arrow(305,240,350,240);arrow(412,220,412,175)
  arrow(350,150,305,150);arrow(180,150,135,150);arrow(67,125,170,70)
  arrow(412,125,260,70);arrow(300,45,345,45)
 return d

def normalized(path):
 return Path(path).read_text(errors='replace').replace('\r','')
def log(n,name):return normalized(repo/f'assignment{n:02}/logs'/name)
def compact(s):return '\n'.join(l for l in s.splitlines() if l.strip())
def footer(canvas,doc):
 canvas.setFont('Body',8);canvas.setFillColor(colors.HexColor('#567083'))
 canvas.drawString(52,28,'SE205068 | Mai The Tam | LOS201')
 canvas.drawRightString(543,28,str(doc.page))
def build(n,pages):
 lab=repo/f'assignment{n:02}'
 path=lab/f'bao_cao/SE205068_MaiTheTam_Asgn{n:02}_BaoCao.pdf'
 story=[]
 for i,(title,items) in enumerate(pages):
  if i:story.append(PageBreak())
  story.append(Paragraph(html.escape(title),styles['Heading']))
  for item in items:
   if isinstance(item,str):story.append(text(item))
   else:story.append(item)
 doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=52,leftMargin=52,topMargin=46,bottomMargin=48,title=f'Assignment {n:02} - Mai The Tam - SE205068',author='Mai The Tam')
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 print(path)

p1=[]
def a1(title,*items):p1.append((title,list(items)))
a1('Assignment 01 - Driver interfaces',
 Paragraph('How to Write a Device Driver',styles['Cover']),
 'Mai Thế Tâm\nStudent ID: SE205068\nCourse: LOS201\nTarget: Linux 5.15, ARMv7 Cortex-A9, QEMU vexpress-a9',
 'This report examines two implemented interfaces: a fixed-major character driver with ioctl commands, and a misc counter device. The design emphasizes explicit ABI boundaries, coherent statistics, bounded user copies, partial-read behavior, and cleanup on every initialization failure.',
 'Scope of evidence: both modules were cross-compiled and executed inside ARM QEMU. The results are software emulation results, not measurements on physical hardware. Source files, executable tests, and complete console/dmesg logs accompany this report.',
 'The ioctl driver is named asgn1_driver and creates /dev/asgn1 at major 241. The independent misc driver creates /dev/counter at major 10 with a dynamic minor. Existing LAB02 device names and binaries are not replaced by these assignment devices.',
 'Reading guide: architecture; ABI and mode design; synchronization and resource ownership; counter semantics; driver comparison; test evidence; theory; reproduction and references.')
a1('1. Architecture and interface boundaries',diagram(1),
 'Applications enter through read(), write(), or ioctl(). VFS resolves the opened character device to its file_operations table. The ioctl callback validates the complete encoded request before copying arguments. GET_STATS copies a local, coherent snapshot back to userspace; SET_MODE copies an integer into kernel memory before updating shared state.',
 'The diagram includes both drivers because their userspace-facing system calls are similar even though registration differs. The proc files use seq_file callbacks rather than the character-device read callback. This separation lets diagnostics inspect state without consuming device data or incrementing the device open/read counters.',
 'Data-plane traffic uses read/write; mode changes, reset, version, and structured statistics use the control plane. No userspace pointer is retained after a syscall returns. Internal memcpy is used only between valid kernel buffers; user transfers use uaccess helpers.')
a1('2. ioctl ABI and state transitions',
 table([['Command','Direction / size','Behavior'],['RESET_BUFFER','_IO / 0','Clear all buffer bytes and read/write counters'],['GET_STATS','_IOR / 20','Return five 32-bit integer fields'],['SET_MODE','_IOW / 4','0: prefix [KERNEL]; 1: raw echo'],['GET_VERSION','_IOR / 64','Return zero-filled bounded version string']],[135,100,256]),
 'The ABI header is shared by the module and the test executable. It uses magic T, request numbers 0 through 3, and fixed-size int fields on the tested ARM EABI and x86_64 ABI. No pointers, long values, or compiler-dependent enums occur in the exported stats structure.',
 'For GET_STATS, the captured ARM command is 0x80145401: _IOC_NR gives 1, _IOC_TYPE gives 0x54, and _IOC_SIZE gives 20. The high direction bits encode a transfer to the caller. Direction names are from the userspace point of view. Matching only the request number would accidentally accept malformed commands with incompatible sizes; the switch matches the full command value.',
 'Echo mode is the load-time default. Kernel mode prefixes exactly eight bytes, [KERNEL], without adding a space. last_write_size records accepted payload bytes, whereas buffer_len includes the prefix. RESET preserves open_count and the selected mode, but resets read_count, write_count, buffer_len and last_write_size.',
 'Unknown commands return ENOTTY, invalid mode values return EINVAL, and bad argument pointers return EFAULT. GET_VERSION uses a 64-byte initialized local array, avoiding leakage of uninitialized stack bytes.')
a1('3. Buffer safety, counters and lifetime',
 'The internal buffer capacity is 1024 bytes, including the trailing NUL. A write accepts at most capacity minus one minus the active prefix length. It first copies payload to a temporary kernel buffer, then commits the fully formed string and metadata while holding data_lock. A failed copy_from_user cannot partially overwrite previously stored data.',
 'The same mutex covers reads, writes, resets, mode changes and statistics snapshots. read_count counts successful read calls returning positive data, rather than open calls or EOF probes. write_count counts successful nonempty writes. Zero-length writes return zero without changing state. proc output holds the mutex while formatting related fields.',
 'Mutexes are suitable because user copies can fault and sleep. A spinlock must not surround such operations. GET_STATS releases the mutex after creating the local snapshot, before copying it out: the result is coherent at snapshot time, although another writer can change the live device immediately afterward.',
 'Initialization acquires resources in order: character major, class, device, proc entry. Each failure label reverses exactly the successful earlier steps. Exit removes proc first, then the device, class and character registration. file_operations.owner is THIS_MODULE, so an open device pins the module.',
 'No asynchronous worker or timer is needed. Writes temporarily allocate a bounded kernel payload buffer, then free it before returning. This avoids a 1 KiB stack frame warning on ARM. Each successful syscall completes all its accesses; no user buffer address escapes into shared state.')
a1('4. Misc counter: atomic state and EOF',
 'The counter driver uses misc_register with MISC_DYNAMIC_MINOR. The misc subsystem supplies major 10 and chooses a free minor. Device creation is delegated to the device model/devtmpfs. It does not reserve another experimental major using register_chrdev.',
 'The value uses atomic_t and atomic_read, atomic_set and atomic_inc as required. A mutex additionally serializes the compound operation of taking the current value, incrementing it, and updating total_reads. An atomic increment alone would not make an independently loaded return value and the statistics snapshot mutually consistent.',
 'Each open file description receives a small kzalloc-owned reader_state. Its first nonempty read creates one decimal snapshot and increments the global counter once. Partial reads consume that same snapshot using simple_read_from_buffer and the file offset. Once all bytes are consumed, the callback returns zero. The release callback frees the per-open state.',
 'This snapshot policy prevents a one-byte reader from combining digits from different counter values. The test uses dd with bs=1 to verify the full string 123 and EOF. Separate cat invocations create separate opens and therefore consume successive values.',
 'Writes accept bounded ASCII strings, reject embedded NUL bytes, call kstrtoint, reject negative values, and update total_writes only after successful validation. The extra overflow policy wraps INT_MAX to zero after returning INT_MAX once, preserving nonnegative output. That boundary policy is explicit rather than relying on signed overflow.')
a1('5. Character, block and network devices',
 table([['Criterion','Character','Block','Network'],['Operation interface','file_operations','block_device_operations + blk-mq','net_device_ops'],['Transfer unit','Bytes / records','Sectors and requests','Packets / frames'],['Buffering','Driver-defined; no universal cache','Page cache and block queues; direct I/O can bypass cache','skb queues, socket buffers, NAPI'],['Embedded example','UART, sensor control','eMMC, SD, NVMe','Ethernet, Wi-Fi'],['Typical access','open/read/write/ioctl','Filesystem or raw block I/O','Sockets, network stack']],[82,133,138,138]),
 'A sensor with short control records is a character-device candidate: it needs read/write and a few configuration requests, not filesystem sectors. A bulk data logger backed by eMMC should use the existing block device and filesystem; introducing a custom byte-stream driver would lose standard caching and filesystem integration.',
 'A packet interface such as an Ethernet controller belongs in the network subsystem. Exposing frames only through a custom character device would bypass routing, sockets, protocol handling, and the usual network management tools. A custom serial protocol on a UART may still remain a character interface because the hardware abstraction is a serial byte stream.',
 'For a small single-purpose counter, miscdevice reduces registration boilerplate. A fixed major character driver is useful here to study the explicit registration path, but fixed numbers require coordination and can collide. Neither framework changes the need for safe callbacks, lifetime management and synchronization.')
# Keep full executable test evidence in the report, not just a PASS statement.
a1('6. ioctl verification on ARM',
 'The userspace tester opens the device, verifies the default echo mode, selects kernel mode, checks all five statistics fields, reads the version, tests invalid mode/command/pointer, and resets the device. The excerpt below is the real terminal capture; repeated dmesg playback is retained in the separate full log.',
 code('\n'.join(compact(log(1,'test_asgn1_output.txt')).splitlines()[:32])),
 'The first GET_STATS result is asserted by the executable, not merely printed: open_count=3, write_count=2, read_count=2, buffer_len=12 and last_write_size=4. After reset, both read/write counters and buffer length are asserted zero; a fresh read must return EOF immediately.')
a1('7. Counter verification and debugging',
 code('\n'.join(compact(log(1,'test_counter_output.txt')).splitlines()[:24])),
 'The three proc snapshots show the required phases: before writes, after setting 100, and after resetting zero. Invalid negative and nonnumeric writes return EINVAL. The script also verifies two successive reads yield 0 then 1, and a one-byte reader terminates without an infinite loop.',
 'A real build problem occurred while preparing the target kernel: the assembler rejected dmb ish with the selected processor mode. The configuration selected ARMv7, but the toolchain invocation needed an explicit architecture flag. Rebuilding with KCFLAGS=-march=armv7-a produced the Cortex-A9 image and enabled the subsequent module builds. The build command is preserved in the support scripts.',
 'The test logs show clean module unload messages. The first external module emits the normal out-of-tree taint notice; that notice is not an Oops or failed insertion. The kernel also prints unrelated emulated display/flash messages during boot and poweroff. Driver validation distinguishes those platform messages from module failures.')
a1('8. Theory: module lifetime and user access',
 'Reference counting: file_operations.owner identifies the owning module. VFS obtains a module reference while a file using these operations remains open and drops it when the final reference to the file is released. Explicit try_module_get/module_put can manage additional references when a subsystem needs them. Initialization references and all callback lifetimes must also be respected.',
 'A normal rmmod of a driver with a held-open device fails because the module is in use. The safe procedure is to stop users, close every inherited or duplicated descriptor, and retry. Forced removal uses rmmod -f only if CONFIG_MODULE_FORCE_UNLOAD permits it; it can leave executable callbacks pointing into freed code and cause corruption or a kernel crash. The assignment tests do not force unload.',
 'User copies: a userspace virtual address belongs to the current process address space, may be unmapped, read-only, or paged out, and can change during the operation. copy_to_user checks access constraints and uses exception-table handling so faults become a failed copy rather than an unhandled kernel exception.',
 'The MMU does not translate a pointer according to the C variable type. It applies page tables and privilege/access permissions. On ARM, protections such as PAN or software equivalents can restrict kernel access to user mappings. Direct dereference may fault or violate the uaccess contract even if an address appeared valid earlier. memcpy alone supplies neither the required validation nor recoverable fault behavior. Never treat user pointers as trusted kernel pointers.')
a1('9. Theory, reproduction and references',
 'MTD models raw flash erase/read/write geometry, eraseblocks, bad blocks and out-of-band data. Raw NAND and NOR can require MTD-aware filesystems such as UBIFS or JFFS2. eMMC and managed SD expose logical sectors behind an internal flash controller and normally belong to the block layer; their internal physical NAND does not mean applications should access them as raw MTD.',
 'EOF handling: cat repeatedly calls read until it receives zero, an error, or is interrupted. The kernel dispatches each userspace read through VFS into the driver; VFS does not invent an EOF merely because the callback previously returned one number. Without offset/snapshot handling, an always-positive driver would feed cat forever and continuously increment the counter.',
 code('bash assignment_support/scripts/run-qemu.sh 1\n# In the guest:\n/opt/asgn1/task1_ioctl/test_asgn1.sh\n/opt/asgn1/task2_misc/test_counter.sh'),
 'Rebuild with the included kernel configuration and ARM GNU toolchain, then set KDIR and run assignment_support/scripts/build.sh. make and make clean are supported in both module directories. The kernel archive/build tree is intentionally excluded from Git; the resulting boot image, DTB, configuration and modules are included.',
 'References: Linux 5.15 source, include/linux/fs.h, miscdevice.h, atomic APIs, lib/kstrtox.c and libfs.c; official ioctl guide: https://docs.kernel.org/driver-api/ioctl.html ; ioctl encoding: https://kernel.org/doc/html/v6.9/userspace-api/ioctl/ioctl-number.html ; Linux read/ioctl manuals: https://man7.org/linux/man-pages/man2/read.2.html and https://man7.org/linux/man-pages/man2/ioctl.2.html . References informed API usage; test outputs are from the included implementation.')

a1('Appendix - Complete ioctl test output', code(compact(log(1,'test_asgn1_output.txt'))))

# Assignment 02 content is appended below, then both reports are generated.
p2=[]
def a2(title,*items):p2.append((title,list(items)))
a2('Assignment 02 - Sensor Monitoring System',
 Paragraph('Embedded Application Design',styles['Cover']),
 'Mai Thế Tâm\nStudent ID: SE205068\nCourse: LOS201\nPlatform: ARMv7 Cortex-A9 in QEMU, Linux 5.15',
 'This document describes a four-thread monitoring application connected to an implemented kernel sensor simulator. It covers data ownership, queueing, shutdown, memory, debugging, system-call behavior and measured wake-up jitter. It reports measured behavior separately for the ARM driver backend and the explicitly selected HOST simulator.',
 'Deliverables include modular C source, ARM and x86_64 executables, the sensor module, a bootable initramfs, kernel configuration, executable scripts, and raw logs. Experimental values in this report are loaded from those logs by the report generator, rather than typed into the source as assumed results.',
 'The scope is an emulated industrial-monitoring workload. Random measurements exercise the alarm logic; they do not model a physical sensor calibration, an actual fieldbus, or a certified hard real-time system. Conclusions about timing are restricted to this software, host load and virtual platform.')
a2('1. Architecture and data flow',diagram(2),
 'The kernel exposes one CSV sample per offset-zero read. Sensor Thread is the sole owner of the device descriptor during operation. It parses the CSV, records wake-up error, and attempts a nonblocking push into the bounded circular buffer. Processor Thread owns the rolling window and publishes alarms and processed-sample messages.',
 'Alert Thread consumes alarm messages, updates its private type counters and forwards human-readable messages to the log queue. Logger Thread alone owns the FILE pointer, formatting timestamps, flushing and rotating. This avoids concurrent stdio operations from time-critical threads.',
 'The main thread coordinates lifecycle and joins the four workers. Five tasks therefore appear in /proc/PID/status. Diagnostic procfs reads are independent of application logging and do not consume additional sensor samples.')
a2('2. Sensor driver contract',
 'The sensor driver registers a misc device named sms_sensor. The CSV record consists of monotonic timestamp milliseconds, temperature and humidity, followed by newline. Random temperatures are generated as integer tenths from 150 through 450; humidity uses tenths from 300 through 900. Integer formatting exports decimal values without executing floating-point instructions in kernel context.',
 'A mutex covers the global interval, timestamp, last values, sample counter and proc snapshot. Each opened file description has a separate bounded CSV snapshot. A successful offset-zero generation increments read_count once; subsequent partial reads consume that snapshot, and a read at its end returns EOF. Userspace seeks back to offset zero for the next sample.',
 'SMS_SET_INTERVAL accepts an unsigned integer pointer, rejects zero and values above 60000 ms, and returns ENOTTY for unknown requests. The driver returns EAGAIN if the minimum interval has not elapsed. The application treats EAGAIN, EINTR and EOF as retryable conditions instead of corrupting a sample or silently terminating.',
 'The assignment names ktime_get_ms(), but Linux 5.15 has no helper with that name. This implementation uses ktime_to_ms(ktime_get()) to obtain the same monotonic-millisecond quantity. Uptime uses div_u64 because native 64-bit division in an ARM32 module can otherwise generate an unresolved __aeabi_uldivmod reference.',
 'Initialization creates the misc registration then proc entry. Failure to create proc deregisters misc. Exit removes both. The module owner pins callbacks while device descriptors remain open; forced removal is not used.')
a2('3. Application lifecycle and configuration',
 table([['State','Entry / exit conditions','Ownership'],['INIT','Validate CLI, allocate, open driver, ioctl, create queues, lock memory','Main owns all resources'],['RUNNING','Create Logger, Alert, Processor, Sensor; sample until duration, sample limit, signal or error','Workers own their assigned data'],['SHUTDOWN','Stop producer; close buffer; drain processor, alarm queue and log queue; join workers','Main reclaims after joins']],[83,242,166]),
 'Defaults are interval 500 ms, temperature threshold 40 degrees Celsius, humidity threshold 80 percent, duration 60 seconds and Sensor FIFO priority 50. Flags -i, -t, -h, -d and -v follow the assignment. Additional explicit switches select OTHER scheduling, the HOST simulator, a sample limit, and configurable device/log/jitter paths.',
 'CLI parsing rejects missing or malformed numbers, negative unsigned settings, zero intervals, nonfinite thresholds, and unexpected positional arguments. Opening a missing real device returns a nonzero exit status. Failing FIFO scheduling or mlockall is reported as an error for an RT run, not silently replaced by OTHER.',
 'SIGINT and SIGTERM handlers set only volatile sig_atomic_t interrupted. They never lock, allocate, print, or call message-queue functions. Main observes the flag and initiates the normal shutdown path. Runtime errors set atomic stop and failed flags. A normal finite run or clean SIGINT returns zero; initialization/runtime failures return nonzero.')
a2('4. Circular buffer and rolling statistics',
 'The buffer allocates 64 SensorData entries once on the heap. It maintains head, tail, current size, closed status, produced, consumed and overflow counters under one mutex. Sensor does not block when the ring is full: it increments overflow and emits a warning through the logging mechanism. This policy favors sampling cadence over guaranteed delivery under overload.',
 'Processor waits on a condition variable while size is zero and the buffer is not closed. The wait is inside a while loop so spurious wake-ups cannot cause a read from an empty ring. Closing the buffer broadcasts the condition; Processor drains accepted entries before returning. The getter copies all exposed statistics under the same mutex.',
 'A ring has predictable memory use and O(1) push/pop with no per-sample malloc. A linked list would introduce allocation failures, fragmentation and less predictable cache behavior. The capacity is a burst allowance, not an unlimited guarantee against a stalled consumer.',
 'Processor privately owns a ten-element rolling window, index, sample count and temperature/humidity sums. Before the window fills, averages divide by the actual available count. Once full, the oldest contribution is subtracted before the new value is inserted. These variables require no mutex because no other thread accesses them.',
 'Alarms use the current measurement for high-temperature/high-humidity checks and compare consecutive raw temperatures for a spike greater than 5 degrees. Rolling averages are logged for analysis, rather than delaying a threshold alarm until ten samples accumulate. The first sample has no predecessor, so no spike alarm is generated for it.')
a2('5. POSIX queues and backpressure',
 'Two POSIX message queues separate alarm delivery from log delivery. Names include the PID and are created with O_CREAT|O_EXCL and mode 0600. Each queue is immediately unlinked after successful creation: open descriptors remain valid, but a crash will not leave a named queue requiring manual removal. Attributes request ten messages, within the standard Linux msg_max default.',
 'Alarm messages contain a timestamp, integer type, explicit reserved field, value and threshold. The explicit reserved field replaces implicit compiler padding and is initialized to zero. This matters because mq_send transfers the entire structure representation, including padding bytes, not merely its logical members.',
 'Timed queue operations block during normal empty/full conditions and periodically check lifecycle flags. They avoid permanent waits after a peer has failed or after a producer has finished. Timeout is an expected control event, not itself an application error. Unexpected queue errors set the failure status.',
 'No queue send/receive occurs while holding the circular-buffer mutex. Processor releases the buffer lock before formatting or sending a message. This prevents a full queue from holding up the producer through an unrelated lock. Backpressure can still slow processing, which is measured via overflow_count rather than hidden by unbounded allocation.',
 'POSIX mq fits small typed alarms and provides blocking notification and message boundaries. Shared memory would avoid a kernel copy but would require a separate notification protocol, ownership rules and queue implementation. For this low-rate workload, the simpler explicit message semantics outweigh that potential optimization.')
a2('6. Synchronization and shutdown proof',
 table([['Shared object','Protection / owner','Observation point'],['Ring entries and counters','buffer.mutex + condition variable','buffer_stats snapshot'],['stop and done flags; failure','C11 atomic operations','All worker loops'],['Signal notification','volatile sig_atomic_t','Main polling loop'],['Sensor fd and jitter array','Sensor-only during run','Main after join'],['Rolling window','Processor-only','Processed log messages'],['Alarm type counts','Alert-only during run','Main after join'],['Log FILE and rotation','Logger-only','Files after close'],['Driver global state','sensor_lock mutex','proc snapshot']],[157,185,149]),
 'There is only one application data mutex, and it is never held across a queue call or a join. Condition waits atomically release that mutex while sleeping. Consequently the application lock graph has no nested-lock cycle. Queue dependencies flow Sensor -> Processor -> Alert/Logger, with no consumer waiting for a resource held by an upstream producer.',
 'Main joins in reverse creation order: Sensor, Processor, Alert, Logger. Sensor closes the ring. Processor exits after draining it and sets processor_done. Alert drains alarms and exits on a subsequent empty timeout. Logger drains logs after alert_done, then closes the file. No producer can enqueue a later log once that completion condition is established.',
 'Partial initialization also sets completion flags for workers that were never created. This lets already-started consumers terminate. Runtime logger failure sets logger_done so app_log fails promptly instead of blocking forever. Alarm publication uses timed sends and checks alert_done for the same reason. This is a bounded shutdown protocol, not cancellation of arbitrary lock-owning threads.')
a2('7. Logging, file ownership and validation',
 'Logger receives messages from both Processor and Alert, prefixes event messages with local realtime date/time and milliseconds, and appends to the configured path. Sensor start/overflow/retry and worker startup messages make the execution paths visible. Logger itself writes an initial startup marker.',
 'Flush is checked against CLOCK_MONOTONIC approximately every five seconds, using receive timeouts to wake even without messages. fclose performs the final flush. Rotation checks the logical FILE position after each line: above 1 MiB, it closes the file, renames it to the .1 path and opens a new file. One previous generation is retained, bounding disk growth.',
 'Only Logger manipulates the file. Sensor and Processor therefore avoid acquiring a file lock or flushing per sample. A logging I/O error stops the application and causes a nonzero return rather than reporting a clean run with missing evidence.',
 code(log(2,'extra_tests.txt')),
 'The rotation test preloads a temporary log above the threshold, runs the application, checks a .1 generation exists and verifies the current file is below the rotation threshold. It uses an isolated temporary directory, preventing accidental replacement of a real user log.',
 'The default device and log paths are macros, with runtime override options. /tmp logs are intentionally ephemeral in the guest. Measurement scripts copy relevant outputs out before shutting down QEMU; the repository logs are therefore durable evidence rather than assumptions about guest persistence.')
# Dynamic evidence sections require the completed measurements.
mem=[]
for t in [5,30,55]:
 s=log(2,f'memory_{t}.txt')
 get=lambda k: re.search(r'^'+k+r':\s*(.+)$',s,re.M).group(1)
 mem.append([f'{t} s',get('VmSize'),get('VmRSS'),get('VmData'),get('Threads')])
a2('8. ARM integration and memory footprint',
 'The ARM validation run used the real /dev/sms_sensor backend at 500 ms for 60 seconds with FIFO scheduling. proc read_count was recorded before and after the run; memory was sampled from the same process at the requested times. Main plus four worker tasks remained present.',
 table([['Time','VmSize','VmRSS','VmData','Threads']]+mem,[65,105,105,105,111]),
 code(compact(log(2,'proc_sms_stats_before.txt'))+'\n\n'+compact(log(2,'proc_sms_stats_after.txt'))),
 'VmSize and RSS are unchanged across these snapshots. This is consistent with one-time ring/jitter allocation, fixed worker stacks and bounded queues. It is not a proof against every possible long-running leak; the independent Valgrind/SIGINT test checks dynamic allocation lifetime on HOST.',
 'A minimum interval applies at the driver as well as the application. Wake-up error can make a nominally periodic read arrive slightly earlier than the minimum since the last successful read; such a read receives EAGAIN and is retried at the next period. Therefore jitter wake-up count, produced sample count and driver read_count must be distinguished. The recorded 60-second result lies within the assignment tolerance of about 120 plus or minus ten.')
a2('9. Address-space regions and allocations',
 code('\n'.join(log(2,'maps.txt').splitlines()[:20])),
 'The executable r-x mapping contains application machine code; r-- and rw- mappings contain read-only data, writable globals and relocation-related data. The [heap] region backs malloc allocations such as the ring and jitter array. Private anonymous mappings also serve libc allocator arenas and thread-related storage.',
 'Each worker requests a 256 KiB pthread stack. Anonymous rw- ranges adjacent to inaccessible --- guard pages are consistent with those stacks; libc can merge stack/arena mappings, and maps alone does not reliably assign each anonymous range to a particular worker name. Main has the [stack] region. The full maps capture is included, rather than claiming every anonymous mapping is a stack.',
 'libc.so.6 executable/read-only/writable mappings provide system-call wrappers, pthreads, queues, malloc and stdio on this glibc version. ld-linux-armhf.so.3 is the dynamic linker. The final kernel-provided vectors/vvar or vdso mappings, when shown, support userspace transitions/time access. Shared-library mappings and heap allocations are distinct from the fixed-size SensorData ring.',
 'The jitter array reserves 100000 long entries once. On ARM32 this is approximately 400 KiB; on x86_64 it is approximately 800 KiB. The allocation is capped even for infinite duration; the report explicitly records the number of samples retained. No per-sample heap allocation grows with runtime.')
a2('10. Valgrind and a real memory defect',
 code('\n'.join(compact(log(2,'valgrind_before_fix.txt')).splitlines()[6:17])),
 'The initial run had no leaked heap blocks, but Valgrind detected uninitialized bytes passed to mq_timedsend from detect_alert. The cause was an implicit padding gap in the binary Alarm structure. Initializing visible fields through a compound literal did not make the padding representation initialized for the system call.',
 'The repair adds an explicit reserved integer in the gap, initializes it, and initializes the message array. This produces a fully defined 32-byte message layout on both tested targets. Treating only leak totals as success would have missed this defect.',
 code('\n'.join(compact(log(2,'valgrind_sms.txt')).splitlines()[-9:])),
 'The final HOST run lasted at least 31 seconds before SIGINT, selected the explicit simulator and OTHER scheduling, joined workers and freed all heap blocks. Valgrind reports zero errors. This validates userspace memory behavior; it neither checks kernel allocations nor proves FIFO timing under emulation. Source snapshots and the before/after logs permit inspection of the correction.')
gdb_lines=compact(log(2,'gdb_sms.txt')).splitlines()
a2('11. GDB: multi-thread alert injection',
 'The reproducible batch script selects the alert-logic scenario. It breaks in detect_alert, lists threads and requests thread apply all bt. With scheduler-locking enabled for stepping, it changes the local sample temperature to 45.0, steps to the local temperature assignment and inspects it. Scheduler locking is disabled before continuing so the Alert consumer can run.',
 code('\n'.join(gdb_lines[:14])+'\n... full backtraces: logs/gdb_sms.txt ...\n'+'\n'.join(l for l in gdb_lines if '45' in l)[:900]),
 'The modified value is a debugger injection, not a naturally measured sensor reading. The captured stderr later shows TEMP_HIGH with VALUE 45.0 and THRESHOLD 40.0. The script disables the breakpoint before continuation and the process exits normally after the finite run.',
 'The full session includes call stacks for the sleeping Sensor, condition/queue-waiting consumers, and the main coordinator. Waiting consumers are expected in a low-rate pipeline and are not evidence of deadlock. The final summary and successful process exit demonstrate the pipeline resumed after debugger intervention.')
strace=log(2,'strace_sms.txt')
rows=[]
for l in strace.splitlines():
 p=l.split()
 if len(p)>=5 and re.fullmatch(r'\d+\.\d+',p[0]) and p[-1]!='total':
  try: rows.append((int(p[3]),p[-1],p[0]))
  except ValueError:pass
rows.sort(reverse=True)
a2('12. strace and CPU versus waiting time',
 table([['Top by call count','Calls','% traced syscall time']]+[[s,c,t] for c,s,t in rows[:5]],[235,90,166]),
 'The capture uses strace -f -c for 30 seconds so all worker threads are traced. mq_timedreceive corresponds to blocking alarm/log consumers; futex underlies mutex/condition operations and thread joining; clock_nanosleep drives both absolute sensor periods and main polling. mq_timedsend carries processed samples, alarms and formatted log messages. Writes include stderr alarm output and buffered file writes.',
 'The HOST backend is explicitly simulated: its syscall mix does not include real sensor-device reads. Calls to lseek can also come from stdio file-position queries for rotation. Error totals include expected receive timeouts and futex races; they are not all fatal application errors.',
 code('\n'.join(log(2,'time_sms.txt').splitlines()[:6])),
 'strace percentages partition measured syscall time, including time spent blocked, and cannot be used as user-versus-kernel CPU percentages. The separate time command provides user and system CPU seconds. Both are small compared with approximately 30 seconds elapsed: this configuration is dominated by waiting for periods and IPC, rather than sustained CPU computation. HOST and emulated ARM timing must not be conflated.')
perf_rows=[]
for l in log(2,'perf_sms.txt').splitlines():
 if re.match(r'^\s*\d+\.\d+%\s+sms_app',l):
  perf_rows.append(re.sub(r'\s+',' ',l.strip()))
a2('13. perf: scheduler and IPC cost',
 'The HOST perf capture uses cpu-clock sampling at 997 Hz with call chains, a 10 ms simulator interval and a 30-second run. This higher rate makes pipeline activity visible without claiming that it is the same workload as the required 500 ms ARM validation run. The report uses self overhead with children excluded.',
 code('\n'.join(perf_rows[:8])),
 'The leading captured symbol is a kernel wake-up/spin-unlock path rather than the rolling-average arithmetic. Its call chain includes message-queue sending and waking consumers. That is plausible for a small pipeline whose work per sample is low and whose coordination crosses kernel queues repeatedly.',
 'A concrete optimization would batch routine processed-sample log messages and reduce frequent main-loop polling, while leaving urgent alarms unbatched. A preallocated in-process log ring with a condition variable could reduce mq syscalls, but would require its own bounded ownership protocol and would change the current chosen architecture. Any change should be measured against both wake-up jitter and log latency.',
 'The perf recording was taken before the padding-only IPC repair; its raw perf.data and text report are retained. The repair initializes the same-size message representation and does not change alarm decisions. Thus the profile is an explicitly labeled development snapshot, not falsely presented as a fresh recording of the final binary. Zero lost samples is reported in the capture header; finite sample counts still limit statistical precision.')
jit=[]
for name in ['fifo','other']:
 s=log(2,f'jitter_{name}.txt');vals=dict(re.findall(r'(\w+)=([^\s]+)',s))
 jit.append([name.upper(),vals['samples'],vals['min_us'],vals['avg_us'],vals['max_us'],vals['p99_us']])
fifo=float(jit[0][-1]);other=float(jit[1][-1]);improvement=(other-fifo)/other*100 if other else 0
a2('14. Real-time implementation and results',
 'Sensor uses SCHED_FIFO priority 50 in the default run and SCHED_OTHER only when explicitly requested. It calls clock_nanosleep with CLOCK_MONOTONIC and TIMER_ABSTIME, advancing a fixed expected deadline rather than sleeping relative to the previous completion. This avoids cumulative processing-time drift. mlockall(MCL_CURRENT|MCL_FUTURE) is requested before worker creation; errors are visible.',
 'Each measurement records actual wake-up minus expected wake-up in microseconds. Both comparison runs use the real ARM driver, interval 100 ms and 1000 wake-ups each. This interval reduces experiment duration while the separate 60-second validation tests the default 500 ms configuration.',
 table([['Policy','N','Min us','Avg us','Max us','P99 us']]+jit,[72,55,80,105,90,89]),
 code(log(2,'jitter_fifo.txt')+'\n'+log(2,'jitter_other.txt')),
 f'Using (OTHER P99 - FIFO P99) / OTHER P99, the measured P99 change is {improvement:.2f} percent. A negative value means FIFO was worse in this finite comparison. Scheduling class alone cannot guarantee an improvement under virtual-machine scheduling and changing HOST activity. No result is rounded into a claim of hard real-time behavior.')
a2('15. Timing interpretation and improvements',
 'A monitoring design must choose a timing budget from its actual process requirements. As an illustrative engineering budget for a 500 ms reporting sensor, 5 ms wake-up error is one percent of the sampling period. That is an explicit design assumption, not an industrial standard or a universal safe bound. Fast control or protection systems can need much tighter deadlines.',
 f'The measured worst wake-up errors are {jit[0][4]} us for FIFO and {jit[1][4]} us for OTHER in the 100 ms experiments. Both observed maxima exceed the illustrative 5000 us budget, so this experiment does not satisfy that chosen maximum-error criterion. A sampled maximum is only the largest event observed, not a proven worst-case execution or scheduling bound. The 500 ms run has its own raw jitter report.',
 'PREEMPT_RT can reduce nonpreemptible kernel sections and change interrupt handling, but it does not remove HOST scheduling delays from QEMU. CPU isolation, controlled IRQ affinity, pinning related workloads, priority-inheritance mutexes, and minimizing work in Sensor are candidates for a physical target. Each adds operational constraints and requires measurement under representative load.',
 'The current mutex is short-lived and no queue calls are performed while it is held. Still, FIFO priority does not imply priority inheritance for a default pthread mutex. A lower-priority Processor holding the ring lock can delay Sensor; configuring PTHREAD_PRIO_INHERIT and measuring contention would be a focused follow-up if the latency budget demands it.',
 'Missing wake-ups are not made invisible: the application advances absolute deadlines and records errors, and the driver enforces its own minimum interval. A late wake-up followed by a catch-up can cause EAGAIN. Improving that behavior would require an explicit policy for skipping missed periods or matching driver interval to acceptable early-arrival tolerance, with corresponding changes to sample-count expectations.')
a2('16. Reproduction, limits and references',
 code('bash assignment_support/scripts/run-qemu.sh 2\n# In QEMU:\ntest_arm.sh\n# Compare 1000 wake-ups per policy:\nsms_app -i 100 -d 0 --samples 1000 --jitter /tmp/fifo.txt\nsms_app -i 100 -d 0 --samples 1000 --other --jitter /tmp/other.txt'),
 'The kernel configuration enables POSIX_MQUEUE and HIGH_RES_TIMERS; the original LAB01 configuration did not. The initramfs mounts proc, sysfs, devtmpfs, tmpfs and mqueue. ARM libc and loader are carried forward from the LAB03 tool image. Build with make host / make arm, or use the shared support script with KDIR pointing at the built ARM Linux tree.',
 'Verification scope: kernel-module build and ARM integration, 60-second execution, proc sample-count checks, three memory snapshots, clean SIGINT, HOST Valgrind, GDB alert injection, strace, perf, rotation and invalid-argument tests, and two real ARM jitter runs. The collected logs are retained even when they show a defect or a scheduling result less favorable than expected.',
 'No physical sensor, persistent flash deployment, PREEMPT_RT comparison kernel, network publication or hard deadline guarantee is claimed. HOST simulator profiles exercise application/IPC paths and exclude the kernel sensor implementation. Reproducing numerical values exactly is not expected because random samples, HOST activity and scheduler behavior vary.',
 'Primary references: Linux 5.15 kernel source and Documentation/driver-api/ioctl.rst; https://docs.kernel.org/driver-api/ioctl.html ; https://man7.org/linux/man-pages/man7/mq_overview.7.html ; https://man7.org/linux/man-pages/man2/clock_nanosleep.2.html ; https://man7.org/linux/man-pages/man2/mlockall.2.html ; https://man7.org/linux/man-pages/man7/sched.7.html ; https://man7.org/linux/man-pages/man7/pthreads.7.html . API documentation informed the implementation; experimental data comes from the accompanying logs.')
if __name__=='__main__':
 build(1,p1)
 build(2,p2)
