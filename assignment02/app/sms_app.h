#ifndef SMS_APP_H
#define SMS_APP_H
#define _GNU_SOURCE
#include "circular_buffer.h"
#include "../driver/sms_sensor.h"
#include <stdatomic.h>
#include <mqueue.h>
#include <time.h>
#define SMS_LOG_PATH "/tmp/sms.log"
#define MESSAGE_SIZE 320
#define JITTER_CAPACITY 100000
#define SENSOR_PRIORITY 50
#define SENSOR_STACK (256 * 1024)
typedef struct { uint64_t timestamp; int type, reserved; double value,threshold; } Alarm;
typedef struct {
    unsigned interval_ms,duration,sample_limit;
    double temp_threshold,humidity_threshold;
    bool verbose,simulate,other;
    const char *device,*log_path,*jitter_path;
} Config;
typedef struct {
    Config config;
    CircularBuffer buffer;
    mqd_t alarms,logs;
    atomic_bool stop,sensor_done,processor_done,alert_done,logger_done;
    atomic_int failed;
    int fd;
    long *jitter;
    size_t jitter_count;
    unsigned long alert_counts[3];
} App;
void *sensor_thread(void *);
void *processor_thread(void *);
void *alert_thread(void *);
void *logger_thread(void *);
void app_error(App *,const char *);
int app_log(App *,const char *,...);
struct timespec deadline_after_ms(unsigned);
int64_t timespec_diff_us(const struct timespec *,const struct timespec *);
#endif
