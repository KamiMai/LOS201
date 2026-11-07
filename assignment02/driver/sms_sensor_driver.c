/* Simulated sensor: integer tenths internally, decimal CSV externally.
 * Mai The Tam - SE205068 - LOS201, 2026-11-07.
 */
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/miscdevice.h>
#include <linux/uaccess.h>
#include <linux/random.h>
#include <linux/ktime.h>
#include <linux/mutex.h>
#include <linux/slab.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include "sms_sensor.h"
struct sample_file { char line[80]; size_t len; };
static DEFINE_MUTEX(sensor_lock);
static unsigned int interval_ms = 100;
static u64 read_count, last_ms, start_ms;
static int last_temp, last_humid;
static struct proc_dir_entry *proc_entry;
/* Allocate a CSV snapshot per file description. */
static int sensor_open(struct inode *inode, struct file *file)
{
    file->private_data = kzalloc(sizeof(struct sample_file), GFP_KERNEL);
    return file->private_data ? 0 : -ENOMEM;
}
/* Release the per-open snapshot. */
static int sensor_release(struct inode *inode, struct file *file)
{
    kfree(file->private_data);
    return 0;
}
/* A new sample begins at offset zero; EOF until userspace seeks back to zero. */
static ssize_t sensor_read(struct file *file, char __user *buf, size_t count, loff_t *pos)
{
    struct sample_file *sample = file->private_data;
    u64 now;
    ssize_t ret;
    if (!count) return 0;
    mutex_lock(&sensor_lock);
    if (*pos == 0) {
        now = ktime_get_ms();
        if (read_count && now - last_ms < interval_ms) {
            mutex_unlock(&sensor_lock);
            return -EAGAIN;
        }
        last_temp = 150 + get_random_u32() % 301;
        last_humid = 300 + get_random_u32() % 601;
        last_ms = now;
        read_count++;
        sample->len = scnprintf(sample->line, sizeof(sample->line), "%llu,%d.%d,%d.%d\n",
                        now, last_temp/10, last_temp%10, last_humid/10, last_humid%10);
    }
    ret = simple_read_from_buffer(buf, count, pos, sample->line, sample->len);
    mutex_unlock(&sensor_lock);
    return ret;
}
/* Configure a bounded positive interval through a userspace pointer. */
static long sensor_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    unsigned int value;
    if (cmd != SMS_SET_INTERVAL) return -ENOTTY;
    if (copy_from_user(&value, (void __user *)arg, sizeof(value))) return -EFAULT;
    if (!value || value > 60000) return -EINVAL;
    mutex_lock(&sensor_lock);
    interval_ms = value;
    mutex_unlock(&sensor_lock);
    pr_info("sms_sensor: interval_ms=%u\n", value);
    return 0;
}
/* Return coherent global statistics and monotonic uptime. */
static int sensor_show(struct seq_file *m, void *unused)
{
    mutex_lock(&sensor_lock);
    seq_printf(m, "read_count: %llu\nlast_temperature: %d.%d\nlast_humidity: %d.%d\nuptime_seconds: %llu\ninterval_ms: %u\n",
            read_count, last_temp/10,last_temp%10,last_humid/10,last_humid%10,
            (ktime_get_ms()-start_ms)/1000,interval_ms);
    mutex_unlock(&sensor_lock);
    return 0;
}
static int sensor_proc_open(struct inode *inode, struct file *file)
{
    return single_open(file, sensor_show, NULL);
}
static const struct proc_ops proc_ops = {
    .proc_open=sensor_proc_open,.proc_read=seq_read,.proc_lseek=seq_lseek,.proc_release=single_release,
};
static const struct file_operations sensor_ops = {
    .owner=THIS_MODULE,.open=sensor_open,.release=sensor_release,.read=sensor_read,
    .unlocked_ioctl=sensor_ioctl,.llseek=default_llseek,
};
static struct miscdevice sensor_device = {
    .minor=MISC_DYNAMIC_MINOR,.name="sms_sensor",.fops=&sensor_ops,
};
static int __init sensor_init(void)
{
    int ret;
    start_ms = ktime_get_ms();
    ret = misc_register(&sensor_device);
    if (ret) return ret;
    proc_entry = proc_create("sms_stats",0444,NULL,&proc_ops);
    if (!proc_entry) { misc_deregister(&sensor_device); return -ENOMEM; }
    pr_info("sms_sensor: loaded\n");
    return 0;
}
static void __exit sensor_exit(void)
{
    proc_remove(proc_entry);
    misc_deregister(&sensor_device);
    pr_info("sms_sensor: unloaded\n");
}
module_init(sensor_init);
module_exit(sensor_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Mai The Tam - SE205068");
MODULE_DESCRIPTION("SMS temperature and humidity sensor simulator");
