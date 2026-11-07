/* Atomic misc counter. Mai The Tam - SE205068 - LOS201, 2026-11-07. */
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/miscdevice.h>
#include <linux/uaccess.h>
#include <linux/atomic.h>
#include <linux/mutex.h>
#include <linux/slab.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
struct reader_state { char text[24]; size_t len; bool sampled; };
static atomic_t counter = ATOMIC_INIT(0);
static unsigned long total_reads, total_writes;
/* Also serialize the read+increment compound operation and proc snapshot. */
static DEFINE_MUTEX(counter_lock);
static struct proc_dir_entry *proc_entry;
/* open: allocate per-open read snapshot for file; return errno/0. */
static int counter_open(struct inode *inode, struct file *file)
{
    file->private_data = kzalloc(sizeof(struct reader_state), GFP_KERNEL);
    return file->private_data ? 0 : -ENOMEM;
}
/* release: free per-open state; return 0. */
static int counter_release(struct inode *inode, struct file *file)
{
    kfree(file->private_data);
    return 0;
}
/* read: deliver one stable decimal snapshot per open, even for one-byte reads. */
static ssize_t counter_read(struct file *file, char __user *buf, size_t count, loff_t *pos)
{
    struct reader_state *state = file->private_data;
    ssize_t ret;
    if (!count) return 0;
    mutex_lock(&counter_lock);
    if (!state->sampled) {
        state->len = scnprintf(state->text, sizeof(state->text), "%d\n", atomic_read(&counter));
        /* Never wrap a user-visible nonnegative counter to a negative number. */
        if (atomic_read(&counter) == INT_MAX) atomic_set(&counter, 0);
        else atomic_inc(&counter);
        total_reads++;
        state->sampled = true;
    }
    ret = simple_read_from_buffer(buf, count, pos, state->text, state->len);
    mutex_unlock(&counter_lock);
    return ret;
}
/* write: parse nonnegative ASCII int from user buf; return accepted count/errno. */
static ssize_t counter_write(struct file *file, const char __user *buf, size_t count, loff_t *pos)
{
    char text[32];
    int value;
    if (!count || count >= sizeof(text)) return -EINVAL;
    if (copy_from_user(text, buf, count)) return -EFAULT;
    text[count] = '\0';
    if (memchr(text, '\0', count) || kstrtoint(text, 10, &value) || value < 0) return -EINVAL;
    mutex_lock(&counter_lock);
    atomic_set(&counter, value);
    total_writes++;
    mutex_unlock(&counter_lock);
    return count;
}
/* proc_show: print all stats while holding counter_lock; return 0. */
static int counter_show(struct seq_file *m, void *v)
{
    mutex_lock(&counter_lock);
    seq_printf(m, "counter: %d\ntotal_reads: %lu\ntotal_writes: %lu\n", atomic_read(&counter), total_reads, total_writes);
    mutex_unlock(&counter_lock);
    return 0;
}
/* proc_open: initialize seq_file for file; return 0/errno. */
static int counter_proc_open(struct inode *inode, struct file *file)
{
    return single_open(file, counter_show, NULL);
}
static const struct proc_ops proc_ops = {
    .proc_open = counter_proc_open, .proc_read = seq_read,
    .proc_lseek = seq_lseek, .proc_release = single_release,
};
static const struct file_operations counter_ops = {
    .owner = THIS_MODULE, .open = counter_open, .release = counter_release,
    .read = counter_read, .write = counter_write, .llseek = no_llseek,
};
static struct miscdevice counter_device = {
    .minor = MISC_DYNAMIC_MINOR, .name = "counter", .fops = &counter_ops,
};
/* init: register misc and proc; unwind if proc fails; return 0/errno. */
static int __init counter_init(void)
{
    int ret = misc_register(&counter_device);
    if (ret) return ret;
    proc_entry = proc_create("counter_info", 0444, NULL, &proc_ops);
    if (!proc_entry) { misc_deregister(&counter_device); return -ENOMEM; }
    pr_info("counter: loaded major=10 minor=%d\n", counter_device.minor);
    return 0;
}
/* exit: remove proc and misc registration; no return value. */
static void __exit counter_exit(void)
{
    proc_remove(proc_entry);
    misc_deregister(&counter_device);
    pr_info("counter: unloaded\n");
}
module_init(counter_init);
module_exit(counter_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Mai The Tam - SE205068");
MODULE_DESCRIPTION("Assignment 01 atomic misc counter");
