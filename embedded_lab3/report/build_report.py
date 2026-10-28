#!/usr/bin/env python3
"""Build the lab report from the checked-in experiment logs."""
from pathlib import Path
import json
import re
import textwrap
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    Preformatted, Image, KeepTogether,
)

lab = Path(__file__).resolve().parent.parent
logs = lab / 'logs'
stats = json.loads((logs / 'latency_summary.json').read_text())
fontdir = Path('/usr/share/fonts/truetype/dejavu')
for name, filename in [('Body', 'DejaVuSans.ttf'), ('Bold', 'DejaVuSans-Bold.ttf'), ('Mono', 'DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(fontdir / filename)))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold', italic='Body', boldItalic='Bold')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='ReportBody', fontName='Body', fontSize=9.5, leading=14, spaceAfter=7))
styles.add(ParagraphStyle(name='ReportTitle', fontName='Bold', fontSize=21, leading=27, spaceAfter=13))
styles.add(ParagraphStyle(name='ReportHeading', fontName='Bold', fontSize=13, leading=18, spaceBefore=12, spaceAfter=8, keepWithNext=True))
styles.add(ParagraphStyle(name='ReportSmall', fontName='Body', fontSize=8, leading=11, spaceAfter=5))
styles.add(ParagraphStyle(name='ReportCode', fontName='Mono', fontSize=7.3, leading=10, spaceAfter=9))
story = []

def p(text, style='ReportBody'):
    story.append(Paragraph(text, styles[style]))

def h(text): p(text, 'ReportHeading')

def table(rows, widths):
    formatted = [[Paragraph(escape(str(cell)), styles['ReportSmall']) for cell in row] for row in rows]
    t = Table(formatted, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#D9D9D9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))
    story.append(t)
    story.append(Spacer(1, 9))

def code(text):
    lines = []
    for line in text.expandtabs(4).splitlines():
        lines.extend(textwrap.wrap(line, width=108, replace_whitespace=False, drop_whitespace=False) or [''])
    story.append(Preformatted('\n'.join(lines), styles['ReportCode']))

def read(name): return (logs / name).read_text(errors='replace').replace('\r', '')

def page(): story.append(PageBreak())

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Body', 8)
    canvas.setFillColor(colors.HexColor('#475569'))
    canvas.drawString(44, 27, 'LOS201  |  LAB03')
    canvas.drawRightString(551, 27, f'Trang {doc.page}')
    canvas.restoreState()

p('LAB03 Debug và phân tích hiệu năng', 'ReportTitle')
p('Mai The Tam<br/>MSSV: [chưa cung cấp] &nbsp; Nhóm/lớp: [chưa cung cấp]<br/>Ngày thực hiện: 28/10/2026')
p('Bài thực hành kiểm tra ứng dụng ARM bằng GDB remote, phân tích memory leak trên HOST bằng Valgrind, phân tích syscall và CPU bằng strace/perf, đồng thời đo wake-up latency của kernel HOST. Các kết luận dưới đây dựa trên log thực nghiệm đi kèm repo LOS201.')
h('1 Môi trường và cách tái hiện')
table([
    ['Thành phần', 'Giá trị'],
    ['HOST', 'Ubuntu x86-64; Intel Core i5-8250U, 8 CPU logic'],
    ['Kernel HOST', '7.0.0-34-generic; PREEMPT_DYNAMIC, CONFIG_PREEMPT_LAZY=y; không phải PREEMPT_RT'],
    ['TARGET', 'QEMU vexpress-a9, Cortex-A9, 2 vCPU, RAM 512 MiB, Linux 5.15.0'],
    ['Compiler', 'GCC và arm-linux-gnueabihf-gcc 13.3.0'],
    ['Công cụ', 'GDB/gdbserver 15.1, Valgrind 3.22.0, strace 6.8, perf 7.0.14, cyclictest 2.50, gnuplot 6.0'],
    ['Biên dịch', 'GDB/memory: -g -O0. Profiling: -g -O1 -fno-omit-frame-pointer. Ứng dụng ARM link static.'],
], [110, 397])
p('Gdbserver và strace là gói Ubuntu armhf; loader/libc/libstdc++/libgcc ARM được bổ sung từ sysroot của toolchain. Guest nhận IP 10.0.2.15 qua DHCP. HOST 127.0.0.1:1234 được forward tới guest:1234. Kernel và rootfs nền lấy từ LAB01 và LAB02.')
code('make -C embedded_lab3/apps buggy_app\nbash embedded_lab3/scripts/pack.sh\nbash embedded_lab3/scripts/run-qemu.sh\n# Trong guest:\ngdbserver 0.0.0.0:1234 /usr/bin/buggy_app\n# Trong terminal HOST khác:\nbash embedded_lab3/scripts/debug.sh')
p('Rootfs được đóng gói bằng gen_init_cpio của kernel LAB01 để tạo device nodes mà không cần root. Toàn bộ lệnh đo và phiên bản công cụ nằm trong scripts/ và logs/environment.txt. Gói nộp chứa initramfs nhưng không chứa zImage/DTB trùng lặp; dùng các file LAB01 trong repo.')

page()
h('2 GDB remote và ba lỗi ứng dụng')
p('Chương trình gốc được giữ riêng, không dựa vào việc nó phải crash. Phiên GDB đã kết thúc bình thường dù có undefined behavior. Comment “Null pointer dereference” trong mẫu không khớp phép truy cập vượt mảng thực tế.')
table([
    ['Lỗi', 'Bằng chứng GDB', 'Nguyên nhân và cách sửa'],
    ['Vượt mảng', 'buggy_app.c:9; i=5, len=5; data chỉ có 5 phần tử. Software watchpoint quan sát i: 5 → 6.', 'Vòng lặp dùng <=. Đổi thành i < len, kiểm tra pointer/length và quy ước số phần tử.'],
    ['Use-after-free', 'buggy_app.c:18-19; buf vẫn ở 0x67da8, nhưng sau free chuỗi chỉ còn “g”.', 'Ownership đã kết thúc khi free. Trả buffer còn sống, kiểm tra malloc, rồi caller free sau khi dùng. Không dùng lại pointer đã free.'],
    ['Signed integer overflow', 'buggy_app.c:24-25; a=b=100000; phép nhân 64-bit = 10000000000; int result = 1410065408.', 'Kết quả vượt INT_MAX. Dùng int64_t và ép kiểu trước phép nhân, hoặc kiểm tra overflow theo miền đầu vào. Signed overflow là undefined behavior.'],
], [100, 197, 210])
p('Tại điểm vượt mảng: pc=0x10468, sp=0x7efffcf8, lr=0x105ec trong phiên đã ghi. Địa chỉ phụ thuộc build và lần chạy. GDB hiển thị backtrace process_data → main, create_message → main và calculate → main. Log đầy đủ nằm ở Phụ lục A và logs/gdb_session.txt.')
p('Software watchpoint được chọn vì target QEMU/kernel không cung cấp hardware watchpoint phù hợp cho thí nghiệm này. Nó kiểm tra giá trị qua stepping nên chậm hơn; chỉ dùng cho chương trình nhỏ có kiểm soát.')

h('3 Memory leak và bản sửa')
table([
    ['Allocation', 'Block', 'Byte mất', 'Vị trí allocation'],
    ['scores', '100', '2000', 'leaky_app.c:20'],
    ['name', '100', '2100', 'leaky_app.c:18'],
    ['message buffer', '50', '12800', 'leaky_app.c:36'],
    ['Tổng definitely lost', '250', '16900', '3 allocation contexts'],
], [150, 60, 80, 217])
p('delete_record chỉ free struct, làm mất các pointer tới name và scores. Vì struct đã được free chứ không còn là một block bị leak, Memcheck báo các allocation con là definitely lost trong lần chạy này; indirectly lost bằng 0. Vòng process_messages mất 50 buffer vì không free sau khi dùng.')
p('Đọc allocation stack từ malloc xuống các caller: create_record → main hoặc process_messages → main. Stack ghi nơi cấp phát; nguyên nhân leak cần đối chiếu thêm với đường giải phóng trong source, không suy ra chỉ từ dòng malloc.')
code('LEAK SUMMARY:' + read('valgrind_report.txt').split('LEAK SUMMARY:')[-1])
p('Bản sửa giải phóng name và scores trước struct, free message buffer sau khi dùng, kiểm tra cấp phát và dọn các allocation đã thành công nếu bước sau thất bại. Source gốc và bản sửa là hai file riêng.')
code(read('valgrind_fixed.txt'))

h('Quan sát bộ nhớ trên ARM')
p('memory_observe_arm chạy cùng workload với hai chế độ leaky/fixed, chờ trước và sau workload để shell đọc /proc khi process còn sống. Đây là helper quan sát; không thay source gốc dùng làm baseline Valgrind.')
table([
    ['Chế độ', 'Thời điểm', 'VmSize kB', 'VmRSS kB', 'VmData kB'],
    ['leaky', 'trước', '624', '4', '152'], ['leaky', 'sau', '624', '4', '152'],
    ['fixed', 'trước', '624', '4', '152'], ['fixed', 'sau', '624', '4', '152'],
], [100, 107, 100, 100, 100])
p('Các counter không đổi trong workload nhỏ này. Allocator có thể dùng arena đã có và giữ lại vùng đã free; RSS cũng không đếm “byte leak” trực tiếp. Vì vậy bảng này không thay thế bằng chứng Memcheck. Memory map cho thấy các vùng text, data, heap và stack; output gốc nằm trong logs/arm_memory.txt.')

page()
h('4 Profiling bằng strace và perf')
p('Giữ perf_target_original.c theo đề và perf_target.c cho bản đo. Bản đo kiểm tra allocation/I/O, dùng mkstemp để tránh dùng chung file /tmp, và thay đổi target tìm kiếm theo vòng lặp. Assembly trước/sau được lưu vì compiler đã hoist các truy vấn giống nhau thành một lần gọi, ngay cả khi chương trình dùng checksum.')
p('Strace/timing HOST và ARM đều dùng 50 vòng heavy_compute. Perf dùng 2000 vòng và 997 Hz để tăng số mẫu, vì lượt 99 Hz trước đó chỉ ghi nhận ba symbol. Không so trực tiếp thời gian hai cấu hình workload khác nhau.')
rows = [['Syscall HOST', '% syscall time', 'Số lần', 'Lỗi']]
for line in read('strace_summary.txt').splitlines():
    fields = line.split()
    if len(fields) >= 5 and re.match(r'^\d+\.\d+$', fields[0]) and fields[-1] != 'total':
        rows.append([fields[-1], fields[0], fields[3], fields[4] if len(fields) == 6 else '0'])
        if len(rows) == 6: break
table(rows, [170, 110, 110, 117])
p('Đây là tỷ lệ trong thời gian syscall được strace thống kê, không phải tỷ lệ thời gian toàn chương trình. Dữ liệu đầy đủ ở strace_full.txt và strace_summary.txt. fprintf có buffering nên 10000 dòng không tạo 10000 lần write; HOST ghi khoảng 70 lần và ARM 76 lần trong các lượt đã lưu.')
rows = [['Symbol', 'Shared object', '% mẫu theo trọng số']]
for line in read('perf_top_symbols.txt').splitlines():
    m = re.match(r'\s*([\d.]+)%\s+perf_target\s+(\S+)\s+\[.\]\s+(.+)', line)
    if m:
        rows.append([m[3], m[2], m[1]])
        if len(rows) == 6: break
table(rows, [240, 137, 130])
p('Bảng giữ đúng symbol mà perf xuất ra; log@plt là trampoline liên kết động, không phải một thuật toán độc lập. Hàm log của libm và heavy_compute chiếm phần lớn mẫu. Call graph nối libm về heavy_compute; chương trình thiên về CPU, không thể kết luận nghẽn I/O chỉ từ strace. Samples và event count đầy đủ nằm trong perf_report.txt; không có lost sample trong bộ cuối.')
code(read('perf_stat.txt'))
p('Counter instructions/cycles dùng để tính IPC cho workload này; cache-misses không phải một tỷ lệ nếu chưa có denominator phù hợp. IPC không có ngưỡng “tốt/xấu” chung cho mọi CPU và chương trình. Flame graph được dựng từ perf_stacks.txt bằng công cụ FlameGraph chính thức; repo giữ SVG, folded stacks và commit của công cụ.')
p('HOST chạy native x86-64, còn ARM chạy dưới QEMU TCG; thời gian ARM chậm hơn không phải phép so sánh tốc độ hai CPU thật. Các syscall, ABI và cách link static/dynamic cũng khác. Bản ARM sau cùng trả checksum 99991021; nó được kiểm tra lại sau thay đổi workload.')

h('5 Latency trên kernel HOST')
p('Đo trực tiếp trên HOST, không đo trong QEMU. Mỗi lượt 60 giây: 4 thread SCHED_FIFO priority 80, pin CPU 0-3, interval 1000 µs, mlockall, histogram 10000 µs. Histogram yêu cầu cùng interval nên distance đặt 0. Cyclictest tạm yêu cầu /dev/cpu_dma_latency=0 µs trong thời gian chạy; không thay sysctl hoặc cấu hình kernel.')
p('Lượt baseline không chủ động tạo stress. Lượt có tải chạy stress-ng với 8 CPU worker, 2 I/O worker và 2 VM worker, vm-bytes=256M, timeout=70s; warm-up 5 giây trước đo. QEMU và HTTP server thử nghiệm được dừng trước bộ latency cuối. Desktop và các dịch vụ HOST vẫn hoạt động, không phải máy đo đã cô lập hoàn toàn.')
rows = [['Chỉ số', 'Không tạo stress', 'Có stress']]
for label, key in [('Min (µs)', 'min_us'), ('Avg gần đúng, gộp thread (µs)', 'avg_us'), ('Max quan sát (µs)', 'max_us'), ('P99 theo histogram (µs)', 'p99_us'), ('Số mẫu', 'cycles'), ('Histogram overflow', 'overflow_count')]:
    vals = [stats[x][key] for x in ('idle','loaded')]
    rows.append([label] + [f'{v:.2f}' if isinstance(v,float) else str(v) for v in vals])
table(rows, [247, 130, 130])
p('Avg gộp được tính theo số cycle của từng thread từ Avg đã làm tròn trong JSON. P99 tính từ histogram gộp; Max lấy trực tiếp từ summary, không lấy bucket cuối. Kiểm tra tổng histogram cùng overflow bằng tổng số cycle.')
image_path = logs / 'latency_histogram.png'
w, height = ImageReader(str(image_path)).getSize()
story.append(KeepTogether([
    Image(str(image_path), width=480, height=480*height/w),
    Paragraph('Trục Y dạng log để nhìn được phần đuôi ít mẫu. Biểu đồ không cắt ở 200 µs vì làm vậy có thể giấu các spike lớn. Đây là phân phối của bốn thread gộp lại.', styles['ReportSmall']),
]))
p('Kết quả một lượt có tải không bắt buộc có Max lớn hơn lượt baseline: Max chịu ảnh hưởng sự kiện hiếm và thời gian quan sát hữu hạn. So sánh đồng thời Avg, P99, Max và điều kiện đo. Không dùng một lần đo để tuyên bố hard real-time hoặc xác lập worst-case bound.')
p('PREEMPT_RT chỉ được phân tích lý thuyết theo D.5; chưa có phép đo trên kernel RT. Kernel lowlatency không đồng nghĩa CONFIG_PREEMPT_RT=y. Với robot yêu cầu response dưới 500 µs, ưu tiên PREEMPT_RT kèm cấu hình priority/affinity, IRQ, bộ nhớ và kiểm thử trên phần cứng đích. Cyclictest chỉ đo wake-up latency, không bao gồm toàn bộ sensor-to-actuator response.')

h('6 Trả lời câu hỏi phân tích')
h('Câu 1 Chuỗi xử lý lệnh next')
p('GDB HOST dùng debug symbols, line table và kiến trúc ARM để xác định nơi cần dừng tiếp theo. next là thao tác source-level step-over: GDB có thể phối hợp single-step và breakpoint tạm để đi qua lời gọi hàm. Không có quy tắc mọi next đều chỉ gửi đúng một packet “next”.')
p('Các yêu cầu điều khiển được gửi qua GDB Remote Serial Protocol trên TCP, qua hostfwd vào gdbserver trong guest. Gdbserver dùng ptrace điều khiển process ARM; khi target dừng vì trap/signal, nó gửi stop reply. GDB lấy registers/memory và ánh xạ pc về source để hiển thị. Gdb-multiarch hỗ trợ ARM registers, ABI và instruction set; một GDB chỉ build cho x86 không mặc định làm được việc này. Phiên thực tế đã đọc pc/sp/lr, backtrace và software watchpoint.')
h('Câu 2 Definitely lost và indirectly lost')
p('Definitely lost nghĩa không còn đường pointer được detector nhận diện tới allocation. Indirectly lost là khi pointer tới allocation chỉ còn qua các block cũng đã bị mất. Trong bài này free(r) được gọi nhưng không free name/scores, nên Memcheck ghi 2100 và 2000 byte definitely lost, không phải indirectly lost. Nếu bản thân r bị leak và vẫn chứa pointer tới các allocation con, phân loại có thể chuyển sang gián tiếp.')
p('Ngoài leak, Memcheck phát hiện invalid read/write, use-after-free, double/invalid free và sử dụng giá trị chưa khởi tạo. Leak check không thay thế kiểm tra lỗi số học; signed integer overflow cần phân tích miền giá trị hoặc công cụ bổ sung. Bản sửa thực tế có 352 allocs/352 frees và ERROR SUMMARY bằng 0.')
h('Câu 3 Tối ưu heavy_compute')
p('Phương án 1: dữ liệu darr không đổi qua các iteration, nên có thể tính tổng sqrt(x)*log(x+1) một lần rồi tái sử dụng hoặc nhân với số iteration nếu chấp nhận khác biệt rounding. Với 50 lượt, phần tính toán lặp có trần cải thiện lý thuyết gần 50 lần; tổng chương trình còn bị giới hạn bởi search, I/O và khởi tạo. Đây là ước lượng theo số phép tính, chưa phải speedup đã benchmark.')
p('Phương án 2: dùng nhiều accumulator/loop unrolling để giảm dependency chain của phép cộng và hỗ trợ scheduling các phép toán độc lập; dữ liệu được duyệt liên tục để giữ locality. Mức tăng cần benchmark, không thể hứa 2x hay 4x từ số lane. Với Cortex-A9, NEON AArch32 không xử lý FP64 vector như mảng double hiện tại; muốn dùng SIMD float32 phải đánh giá sai số, dùng thư viện vector math phù hợp và kiểm tra lại kết quả. log vẫn là phép toán đắt, không có một instruction NEON “log” thay trực tiếp.')
p('Trong bộ perf cuối, log/libm và heavy_compute là các hotspot thật. Việc thay đổi search query trong bản đo nhằm giữ workload có thật, không được trình bày như tối ưu giúp chương trình chạy nhanh hơn.')
question4_start = len(story)
h('Câu 4 Latency spike và PREEMPT_RT')
p('Nguồn 1 là hard IRQ và vùng tắt interrupt/preemption: tác vụ ưu tiên cao vẫn phải chờ. PREEMPT_RT chuyển phần lớn IRQ sang thread để scheduler điều khiển, nhưng các ngoại lệ và low-level raw critical sections vẫn còn.')
p('Nguồn 2 là contention/priority inversion quanh lock. PREEMPT_RT chuyển nhiều spinlock sang sleeping lock dựa trên rtmutex và priority inheritance để tác vụ giữ lock được ưu tiên phù hợp; không biến mọi lock thành preemptible hoặc bỏ mọi đoạn bảo vệ.')
p('Nguồn 3 là page fault, reclaim và hoạt động quản lý bộ nhớ. mlockall, prefault và tránh allocation/I/O không giới hạn trong vòng điều khiển giúp giảm biến thiên; PREEMPT_RT không tự loại bỏ mọi page fault. Ngoài ra SMI/firmware, power management và thiết bị có thể gây spike ngoài khả năng khắc phục hoàn toàn của scheduler. Số liệu Max/P99 của bài phải được đọc cùng cấu hình và tải, không suy rằng Avg thấp là bảo đảm deadline.')
question4 = story[question4_start:]
story[question4_start:] = [KeepTogether(question4)]
h('Câu 5 Chọn công cụ theo triệu chứng')
table([
    ['Triệu chứng', 'Công cụ ưu tiên', 'Lý do và bước tiếp'],
    ['Crash ngẫu nhiên sau vài giờ', 'GDB và core dump', 'Bắt signal, stack, registers; dùng Valgrind nếu nghi UAF/invalid access.'],
    ['Chạy chậm dần theo thời gian', 'Valgrind + /proc', 'Kiểm tra leak và tăng bộ nhớ; bổ sung strace để tìm FD/syscall bị tích lũy hoặc blocking.'],
    ['Đôi khi lỡ deadline', 'cyclictest', 'Đo phân phối/tail wake-up latency dưới tải; tiếp tục trace scheduler/IRQ nếu cần tìm nguyên nhân.'],
    ['Một hàm làm hệ thống chậm', 'perf', 'Lấy mẫu CPU/call graph; dùng strace nếu nguyên nhân thực tế là chờ syscall/I/O.'],
], [157, 125, 225])

h('7 Khó khăn và cách xử lý')
p('<b>Rootfs thiếu cấu hình resolver:</b> gdbserver :1234 không phân giải được tên. Dùng địa chỉ số 0.0.0.0:1234; thêm DHCP script để guest có IP trước kết nối.')
p('<b>Crash khi profiling bằng sudo:</b> mẫu gốc mở file /tmp cố định mà không kiểm tra fopen. File do user tạo trước đó cùng fs.protected_regular=2 khiến luồng mở dưới sudo có thể thất bại, rồi fprintf nhận NULL. Ban đầu chẩn đoán nhầm là lỗi perf và thử bản 6.8; cả hai đều thất bại. Sửa bằng mkstemp và xử lý lỗi I/O; bộ cuối dùng perf 7.0.14, các lệnh đều kết thúc thành công. Log trước sửa được giữ để thể hiện quá trình chẩn đoán.')
p('<b>Compiler thay đổi workload:</b> kết quả search ban đầu không được dùng; sau khi thêm checksum, các truy vấn hệt nhau vẫn bị hoist. Đối chiếu objdump rồi thay đổi truy vấn mỗi vòng để bảo đảm thực thi công việc cần đo.')
p('<b>Giới hạn quyền:</b> sandbox chặn ptrace và HOST đặt perf_event_paranoid=4. Strace/GDB chạy ngoài sandbox; perf và SCHED_FIFO chạy qua sudo. Không hạ perf_event_paranoid toàn hệ thống. File perf.data do root tạo được trả quyền sở hữu cho user sau phép đo.')

h('Tài liệu tham khảo')
for title, url in [
    ('GDB Remote Serial Protocol', 'https://sourceware.org/gdb/current/onlinedocs/gdb.html/Remote-Protocol.html'),
    ('Valgrind Memcheck manual', 'https://valgrind.org/docs/manual/mc-manual.html'),
    ('Linux PREEMPT_RT differences', 'https://docs.kernel.org/core-api/real-time/differences.html'),
    ('Arm C Language Extensions, AArch32 Neon', 'https://arm-software.github.io/acle/main/acle.html'),
    ('FlameGraph tools', 'https://github.com/brendangregg/FlameGraph'),
]: p(f'{title}: <link href="{url}" color="#1D4ED8">{url}</link>', 'ReportSmall')

page()
h('Phụ lục A Toàn bộ phiên GDB')
code(read('gdb_session.txt'))
h('Phụ lục B Allocation stack trước sửa')
code(read('valgrind_report.txt'))
page()
h('Phụ lục C Kết quả ARM và latency theo thread')
code(read('arm_profile.txt'))
p('Thống kê chi tiết theo từng CPU/thread nằm trong cyclic_idle.json, cyclic_loaded.json và latency_summary.json. Các file log còn lại và dữ liệu perf/histogram được nộp kèm để kiểm tra lại, không thay thế bằng output mẫu trong đề. MSSV và nhóm/lớp cần điền trước khi nộp chính thức.')

output = lab / 'report' / 'LAB03_BaoCao.pdf'
doc = SimpleDocTemplate(str(output), pagesize=(595.28,841.89), rightMargin=44, leftMargin=44, topMargin=40, bottomMargin=44, title='LOS201 LAB03 Debug va phan tich hieu nang', author='Mai The Tam')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(output)
