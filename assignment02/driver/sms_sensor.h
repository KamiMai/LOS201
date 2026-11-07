/* Sensor ABI. Mai The Tam - SE205068, 2026-11-07. */
#ifndef SMS_SENSOR_H
#define SMS_SENSOR_H
#include <linux/ioctl.h>
#define SMS_SET_INTERVAL _IOW('S', 1, unsigned int)
#define SMS_DEVICE_PATH "/dev/sms_sensor"
#endif
