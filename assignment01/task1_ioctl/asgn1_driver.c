/* ioctl character device. Mai The Tam - SE205068 - LOS201, 2026-11-07. */
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/device.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include "asgn1_ioctl.h"
#define MAJOR_NUMBER 241
#define CAPACITY 1024
static DEFINE_MUTEX(data_lock);
static char data[CAPACITY];
static struct asgn1_stats stats;
static int mode = 1;
static struct class *asgn_class;
static struct device *asgn_device;
static struct proc_dir_entry *proc_entry;
/* open: inode/file are VFS handles; return 0 after counting successful open. */
static int asgn_open(struct inode *inode, struct file *file)
{
    mutex_lock(&data_lock);
    stats.open_count++;
    mutex_unlock(&data_lock);
    return 0;
}
/* read: copy at most count bytes to user buf from *pos; return bytes or errno. */
static ssize_t asgn_read(struct file *file, char __user *buf, size_t count, loff_t *pos)
{
    ssize_t ret;
    mutex_lock(&data_lock);
    ret = simple_read_from_buffer(buf, count, pos, data, stats.buffer_len);
    if (ret > 0)
        stats.read_count++;
    mutex_unlock(&data_lock);
    return ret;
}
/* write: replace data, adding prefix in mode 0; errors leave previous data intact. */
static ssize_t asgn_write(struct file *file, const char __user *buf, size_t count, loff_t *pos)
{
    char tmp[CAPACITY];
    size_t prefix, accepted;
    if (!count)
        return 0;
    mutex_lock(&data_lock);
    prefix = mode == 0 ? sizeof("[KERNEL]") - 1 : 0;
    accepted = min(count, (size_t)CAPACITY - 1 - prefix);
    if (copy_from_user(tmp + prefix, buf, accepted)) {
        mutex_unlock(&data_lock);
        return -EFAULT;
    }
    if (prefix)
        memcpy(tmp, "[KERNEL]", prefix);
    tmp[prefix + accepted] = '\0';
    memcpy(data, tmp, prefix + accepted + 1);
    stats.buffer_len = prefix + accepted;
    stats.last_write_size = accepted;
    stats.write_count++;
    mutex_unlock(&data_lock);
    return accepted;
}
/* ioctl: dispatch full encoded cmd, arg is a userspace pointer; return 0/errno. */
static long asgn_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    struct asgn1_stats snapshot;
    int requested_mode;
    char version[ASGN1_VERSION_SIZE] = "asgn1_driver v1.0 - SE205068";
    pr_info("asgn1: ioctl cmd=0x%x nr=%u size=%u\n", cmd, _IOC_NR(cmd), _IOC_SIZE(cmd));
    switch (cmd) {
    case ASGN1_RESET_BUFFER:
        mutex_lock(&data_lock);
        memset(data, 0, sizeof(data));
        stats.buffer_len = 0;
        stats.read_count = 0;
        stats.write_count = 0;
        stats.last_write_size = 0;
        mutex_unlock(&data_lock);
        return 0;
    case ASGN1_GET_STATS:
        mutex_lock(&data_lock);
        snapshot = stats;
        mutex_unlock(&data_lock);
        return copy_to_user((void __user *)arg, &snapshot, sizeof(snapshot)) ? -EFAULT : 0;
    case ASGN1_SET_MODE:
        if (copy_from_user(&requested_mode, (void __user *)arg, sizeof(requested_mode)))
            return -EFAULT;
        if (requested_mode != 0 && requested_mode != 1)
            return -EINVAL;
        mutex_lock(&data_lock);
        mode = requested_mode;
        mutex_unlock(&data_lock);
        return 0;
    case ASGN1_GET_VERSION:
        return copy_to_user((void __user *)arg, version, sizeof(version)) ? -EFAULT : 0;
    default:
        return -ENOTTY;
    }
}
/* proc_show: output coherent stats through seq_file m; return 0. */
static int proc_show(struct seq_file *m, void *v)
{
    mutex_lock(&data_lock);
    seq_printf(m, "open_count: %d\nwrite_count: %d\nread_count: %d\nbuffer_len: %d\nlast_write_size: %d\nmode: %d\n",
               stats.open_count, stats.write_count, stats.read_count, stats.buffer_len, stats.last_write_size, mode);
    mutex_unlock(&data_lock);
    return 0;
}
/* proc_open: attach one seq_file snapshot callback to file; return errno or 0. */
static int proc_open(struct inode *inode, struct file *file)
{
    return single_open(file, proc_show, NULL);
}
static const struct proc_ops proc_ops = {
    .proc_open = proc_open, .proc_read = seq_read,
    .proc_lseek = seq_lseek, .proc_release = single_release,
};
static const struct file_operations ops = {
    .owner = THIS_MODULE, .open = asgn_open, .read = asgn_read,
    .write = asgn_write, .unlocked_ioctl = asgn_ioctl, .llseek = no_llseek,
};
/* init: register chrdev, class, device, proc; unwind every failure; return errno/0. */
static int __init asgn_init(void)
{
    int ret = register_chrdev(MAJOR_NUMBER, "asgn1", &ops);
    if (ret < 0) return ret;
    asgn_class = class_create(THIS_MODULE, "asgn1_class");
    if (IS_ERR(asgn_class)) { ret = PTR_ERR(asgn_class); goto unregister; }
    asgn_device = device_create(asgn_class, NULL, MKDEV(MAJOR_NUMBER, 0), NULL, "asgn1");
    if (IS_ERR(asgn_device)) { ret = PTR_ERR(asgn_device); goto destroy_class; }
    proc_entry = proc_create("asgn1_info", 0444, NULL, &proc_ops);
    if (!proc_entry) { ret = -ENOMEM; goto destroy_device; }
    pr_info("asgn1: loaded major=241 mode=echo\n");
    return 0;
destroy_device:
    device_destroy(asgn_class, MKDEV(MAJOR_NUMBER, 0));
destroy_class:
    class_destroy(asgn_class);
unregister:
    unregister_chrdev(MAJOR_NUMBER, "asgn1");
    return ret;
}
/* exit: release registrations in reverse order; no parameters/return value. */
static void __exit asgn_exit(void)
{
    proc_remove(proc_entry);
    device_destroy(asgn_class, MKDEV(MAJOR_NUMBER, 0));
    class_destroy(asgn_class);
    unregister_chrdev(MAJOR_NUMBER, "asgn1");
    pr_info("asgn1: unloaded\n");
}
module_init(asgn_init);
module_exit(asgn_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Mai The Tam - SE205068");
MODULE_DESCRIPTION("Assignment 01 ioctl character device");
