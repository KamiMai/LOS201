# LOS201

Hai bài thực hành Embedded Linux trên ARMv7, QEMU `vexpress-a9` và Cortex-A9. Repo lưu cấu hình, rootfs, driver và các image đã build. Cây nguồn upstream cùng file build trung gian không được đưa vào repo.

## Nội dung

| Thư mục | Nội dung |
| --- | --- |
| `embedded_lab1/configs` | Cấu hình Linux, BusyBox và U-Boot |
| `embedded_lab1/rootfs/initramfs` | Rootfs BusyBox, init và cấu hình khởi động |
| `embedded_lab1/output` | zImage, DTB, U-Boot và initramfs LAB01 |
| `embedded_lab2/driver` | Source, Makefile và module ARM của character driver |
| `embedded_lab2/rootfs/initramfs` | Rootfs LAB02, rcS, module và script kiểm tra |
| `embedded_lab2/output` | Initramfs LAB02 đã đóng gói |
| `FILE_MANIFEST.json` | SHA-256 các file thường được sao chép từ bản thực hành |

## Môi trường

- Ubuntu host x86-64, GCC cross compiler `arm-linux-gnueabihf-`.
- Linux 5.15.0, BusyBox 1.35.0, U-Boot 2022.04.
- QEMU `vexpress-a9`, Cortex-A9, RAM 512 MiB, 2 CPU.

## Chạy image có sẵn

Cài `qemu-system-arm` trên Ubuntu nếu máy chưa có, rồi từ thư mục gốc repo:

```bash
bash scripts/run-qemu.sh 1
bash scripts/run-qemu.sh 2
```

Mỗi lần chọn một bài. Bấm Enter khi BusyBox yêu cầu kích hoạt console. Thoát QEMU bằng Ctrl+A rồi X.

## Kiểm tra LAB02 trong QEMU

```sh
uname -r
lsmod
ls -l /dev/lab2
cat /proc/lab2_info
printf '%s' 'Hello LAB2' > /dev/lab2
cat /dev/lab2
printf '\n'
cat /sys/class/lab2_class/lab2/buffer_len
cat /sys/class/lab2_class/lab2/open_count
cat /sys/class/lab2_class/lab2/last_data
dmesg | grep lab2
```

`Hello LAB2` không có newline dài 10 byte. Module được rcS tự nạp. Các script test hiện giữ nguyên bản thực hành và có lệnh `insmod` riêng; khi test báo `File exists`, gỡ module trước từng script:

```sh
rmmod lab2_driver
test_driver.sh
rmmod lab2_driver
test_procfs.sh
```

## Build lại module

Cần cây Linux 5.15 đã cấu hình và build khớp với kernel đang boot. Từ thư mục gốc repo, thay đường dẫn kernel phù hợp:

```bash
make -C /path/to/linux-5.15 \
  M="$PWD/embedded_lab2/driver" \
  ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- modules

cp embedded_lab2/driver/lab2_driver.ko \
  embedded_lab2/rootfs/initramfs/lib/modules/5.15.0/
```

Sau khi thay module hoặc script phải đóng gói lại initramfs. Module ARM không nạp vào kernel x86-64 của host. Nếu đổi release kernel phải cập nhật đường dẫn module trong rootfs và script.

Git không lưu character device nodes hoặc thư mục rỗng. Bản initramfs trong `output` đã chứa cấu trúc boot; khi dựng lại rootfs từ checkout, cần tạo các thư mục `dev`, `proc`, `sys`, `tmp` và device nodes thiết yếu trước khi đóng gói:

```bash
cd embedded_lab2/rootfs/initramfs
mkdir -p dev proc sys tmp
[ -e dev/console ] || sudo mknod -m 600 dev/console c 5 1
[ -e dev/null ] || sudo mknod -m 666 dev/null c 1 3
[ -e dev/zero ] || sudo mknod -m 666 dev/zero c 1 5
[ -e dev/random ] || sudo mknod -m 666 dev/random c 1 8

(set -o pipefail; find . -print0 | cpio --null -o --format=newc --owner=0:0 | gzip -9 > ../../output/initramfs_lab2.cpio.gz)
```

## MTD và JFFS2

Phần này thực hiện trên Ubuntu host. Dùng `nandsim`, `mtd-utils`, `mtdblock` và `jffs2`. Trước khi xóa hoặc ghi phải xác minh partition thuộc NAND simulator bằng `/proc/mtd` và `mtdinfo`; không giả định mọi máy đều dùng `mtd0`.

Trong phiên đã quan sát, simulator là NAND 32 MiB, eraseblock 16384 byte, page 512 byte. Kiểm tra dữ liệu trước và sau umount/mount bằng SHA-256. Nandsim lưu RAM nên remount persistence không chứng minh dữ liệu sống qua reboot host.

Repo chưa chứa log MTD hoàn chỉnh hoặc báo cáo PDF. Không có kết quả thực hành nào được tạo giả để thay cho log.

## Nguồn upstream

- Linux 5.15: https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.15.tar.xz
- BusyBox 1.35.0: https://busybox.net/downloads/busybox-1.35.0.tar.bz2
- U-Boot 2022.04: https://ftp.denx.de/pub/u-boot/u-boot-2022.04.tar.bz2

Các phần mềm upstream giữ nguyên bản quyền và giấy phép tương ứng; phần mềm upstream không phải do tác giả bài lab viết.

## LAB03

[LAB03](embedded_lab3/README.md) contains remote GDB debugging, Valgrind before/after fixes, host/ARM profiling and host cyclictest measurements. See the [report](embedded_lab3/report/LAB03_BaoCao.pdf) and the [submission archive](embedded_lab3/output/MaiTheTam_Lab03.tar.gz).

## Assignments

- [Assignment 01 - ioctl and misc counter](assignment01/README.md)
- [Assignment 02 - Sensor Monitoring System](assignment02/README.md)
- [Shared ARM build and QEMU environment](assignment_support/README.md)

Student: Mai Thế Tâm - SE205068 - LOS201. Assignment reports and captures
are stored alongside their source; the original lab folders are separate.
