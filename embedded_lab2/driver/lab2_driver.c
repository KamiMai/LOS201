#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/slab.h>
#include <linux/mutex.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Embedded Linux Lab");
MODULE_DESCRIPTION("LAB-02: Simple Character Device Driver");
MODULE_VERSION("1.0");

#define DEVICE_NAME "lab2"
#define CLASS_NAME  "lab2_class"
#define BUFFER_SIZE 1024
#define DRIVER_MAJOR 240
/* 240-254: reserved for local/experimental use */

static int major_number = DRIVER_MAJOR;
static char device_buffer[BUFFER_SIZE];
static int buffer_len = 0;
static int open_count = 0;
static struct class *lab2_class = NULL;
static struct device *lab2_device = NULL;

/*
 * mutex bảo vệ device_buffer / buffer_len khỏi race condition khi
 * nhiều process cùng gọi write()/read() đồng thời (xem Câu 2, Mục VI).
 * Không dùng spinlock vì thao tác copy_from_user()/copy_to_user() có
 * thể ngủ (sleep) khi page bị swap ra, mutex cho phép ngủ còn spinlock
 * thì không.
 */
static DEFINE_MUTEX(lab2_mutex);

/* ===== PROCFS Implementation =====
 * seq_file API: dùng cho các entry /proc có thể sinh dữ liệu dài hơn
 * một trang (4KB) một cách an toàn — tự động quản lý việc gọi lại
 * hàm show() nhiều lần nếu dữ liệu chưa đọc hết. single_open() là
 * helper cho trường hợp đơn giản: toàn bộ nội dung được sinh ra một
 * lần trong hàm show(), không cần iterator phức tạp.
 */
static struct proc_dir_entry *proc_entry;

static int lab2_proc_show(struct seq_file *m, void *v)
{
	seq_printf(m, "LAB-02 Driver Statistics\n");
	seq_printf(m, "======================\n");
	seq_printf(m, "Driver name : %s\n", DEVICE_NAME);
	seq_printf(m, "Major number : %d\n", major_number);
	seq_printf(m, "Buffer size : %d bytes\n", BUFFER_SIZE);
	seq_printf(m, "Data length : %d bytes\n", buffer_len);
	seq_printf(m, "Open count : %d\n", open_count);
	if (buffer_len > 0)
		seq_printf(m, "Last data : [%s]\n", device_buffer);
	return 0;
}

static int lab2_proc_open(struct inode *inode, struct file *file)
{
	return single_open(file, lab2_proc_show, NULL);
}

static const struct proc_ops lab2_proc_fops = {
	.proc_open    = lab2_proc_open,
	.proc_read    = seq_read,
	.proc_lseek   = seq_lseek,
	.proc_release = single_release,
};

/* ===== SYSFS Implementation =====
 * DEVICE_ATTR_RO là macro sinh sẵn struct device_attribute cùng tên
 * dev_attr_<name>, tự nối với hàm <name>_show(). Mỗi attribute trở
 * thành 1 file riêng trong sysfs, gắn với kobject của lab2_device
 * (mọi struct device trong kernel đều nhúng 1 kobject — đó là cơ chế
 * sysfs dùng để biểu diễn cây thiết bị dưới dạng thư mục/file).
 */
static ssize_t buffer_len_show(struct device *dev,
				struct device_attribute *attr, char *buf)
{
	return sprintf(buf, "%d\n", buffer_len);
}

static ssize_t open_count_show(struct device *dev,
				struct device_attribute *attr, char *buf)
{
	return sprintf(buf, "%d\n", open_count);
}

static ssize_t last_data_show(struct device *dev,
			       struct device_attribute *attr, char *buf)
{
	if (buffer_len > 0)
		return sprintf(buf, "%s\n", device_buffer);
	return sprintf(buf, "(empty)\n");
}

static DEVICE_ATTR_RO(buffer_len);
static DEVICE_ATTR_RO(open_count);
static DEVICE_ATTR_RO(last_data);

static struct attribute *lab2_attrs[] = {
	&dev_attr_buffer_len.attr,
	&dev_attr_open_count.attr,
	&dev_attr_last_data.attr,
	NULL,
};

static struct attribute_group lab2_attr_group = {
	.attrs = lab2_attrs,
};

/*
 * lab2_open() - gọi khi userspace open("/dev/lab2").
 * Chỉ tăng bộ đếm open_count dưới mutex để tránh 2 process mở cùng
 * lúc làm giá trị đếm bị race.
 */
static int lab2_open(struct inode *inode, struct file *file)
{
	mutex_lock(&lab2_mutex);
	open_count++;
	mutex_unlock(&lab2_mutex);
	pr_info("lab2_driver: device opened (count=%d)\n", open_count);
	return 0;
}

/* lab2_release() - gọi khi userspace close(fd). */
static int lab2_release(struct inode *inode, struct file *file)
{
	pr_info("lab2_driver: device closed\n");
	return 0;
}

/*
 * lab2_read() - trả dữ liệu trong device_buffer về userspace.
 * Dùng copy_to_user() thay vì memcpy() vì buf trỏ tới vùng nhớ user
 * space (địa chỉ ảo thuộc page table của process gọi read()), khác
 * hẳn không gian địa chỉ kernel. Kernel không được truy cập trực tiếp
 * con trỏ user space bằng memcpy(): copy_to_user() kiểm tra con trỏ có
 * hợp lệ/nằm trong vùng nhớ user không, xử lý page fault nếu trang đó
 * bị swap ra, và trả lỗi -EFAULT thay vì gây kernel panic hoặc lỗ hổng
 * bảo mật (đọc/ghi nhầm vùng nhớ kernel khác) như khi dùng memcpy().
 */
static ssize_t lab2_read(struct file *file, char __user *buf,
			  size_t len, loff_t *offset)
{
	int bytes_read = 0;

	if (*offset >= buffer_len)
		return 0; /* EOF */

	if (len > buffer_len - *offset)
		len = buffer_len - *offset;

	if (copy_to_user(buf, device_buffer + *offset, len)) {
		pr_err("lab2_driver: copy_to_user failed\n");
		return -EFAULT;
	}

	*offset += len;
	bytes_read = len;
	pr_info("lab2_driver: sent %d bytes to user\n", bytes_read);
	return bytes_read;
}

/*
 * lab2_write() - nhận dữ liệu từ userspace vào device_buffer.
 * copy_from_user() là chiều ngược lại của copy_to_user(): kiểm tra
 * vùng nhớ nguồn (user space) hợp lệ trước khi sao chép vào kernel
 * buffer. mutex_lock() bảo vệ device_buffer/buffer_len suốt quá trình
 * ghi để tránh 2 write() đồng thời từ 2 process ghi đè lẫn nhau
 * (race condition, xem Câu 2).
 */
static ssize_t lab2_write(struct file *file, const char __user *buf,
			   size_t len, loff_t *offset)
{
	if (len > BUFFER_SIZE - 1) {
		pr_warn("lab2_driver: write too large, truncating\n");
		len = BUFFER_SIZE - 1;
	}

	mutex_lock(&lab2_mutex);
	if (copy_from_user(device_buffer, buf, len)) {
		mutex_unlock(&lab2_mutex);
		return -EFAULT;
	}
	buffer_len = len;
	device_buffer[buffer_len] = '\0';
	mutex_unlock(&lab2_mutex);

	pr_info("lab2_driver: received %zu bytes: [%s]\n", len, device_buffer);
	return len;
}

static struct file_operations lab2_fops = {
	.owner   = THIS_MODULE,
	.open    = lab2_open,
	.release = lab2_release,
	.read    = lab2_read,
	.write   = lab2_write,
};

/*
 * lab2_init() - entry point khi insmod. Đăng ký character device với
 * major number cố định (240), tạo class + device để udev/mdev tự sinh
 * node trong /dev, rồi tạo /proc/lab2_info và sysfs attribute group.
 */
static int __init lab2_init(void)
{
	int ret;

	pr_info("lab2_driver: initializing module\n");

	ret = register_chrdev(major_number, DEVICE_NAME, &lab2_fops);
	if (ret < 0) {
		pr_err("lab2_driver: register_chrdev failed: %d\n", ret);
		return ret;
	}

	lab2_class = class_create(THIS_MODULE, CLASS_NAME);
	if (IS_ERR(lab2_class)) {
		unregister_chrdev(major_number, DEVICE_NAME);
		return PTR_ERR(lab2_class);
	}

	lab2_device = device_create(lab2_class, NULL,
				     MKDEV(major_number, 0), NULL, DEVICE_NAME);
	if (IS_ERR(lab2_device)) {
		class_destroy(lab2_class);
		unregister_chrdev(major_number, DEVICE_NAME);
		return PTR_ERR(lab2_device);
	}

	/* Tạo /proc/lab2_info */
	proc_entry = proc_create("lab2_info", 0444, NULL, &lab2_proc_fops);
	if (!proc_entry)
		pr_warn("lab2_driver: failed to create /proc/lab2_info\n");
	else
		pr_info("lab2_driver: /proc/lab2_info created\n");

	/* Đăng ký sysfs attribute group */
	ret = sysfs_create_group(&lab2_device->kobj, &lab2_attr_group);
	if (ret)
		pr_warn("lab2_driver: sysfs_create_group failed\n");

	pr_info("lab2_driver: loaded, major=%d\n", major_number);
	return 0;
}

/*
 * lab2_exit() - entry point khi rmmod. Gỡ theo thứ tự ngược lại với
 * lúc tạo: sysfs group -> proc entry -> device -> class -> chrdev.
 */
static void __exit lab2_exit(void)
{
	sysfs_remove_group(&lab2_device->kobj, &lab2_attr_group);

	if (proc_entry)
		proc_remove(proc_entry);

	device_destroy(lab2_class, MKDEV(major_number, 0));
	class_destroy(lab2_class);
	unregister_chrdev(major_number, DEVICE_NAME);
	pr_info("lab2_driver: module unloaded\n");
}

module_init(lab2_init);
module_exit(lab2_exit);
