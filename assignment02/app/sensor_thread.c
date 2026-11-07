/* Absolute-period sampling with optional explicit HOST simulator.
 * Mai The Tam - SE205068 - LOS201, 2026-11-07. */
#include "sms_app.h"
#include "sensor_thread.h"
#include <stdio.h>
#include <errno.h>
#include <unistd.h>
#include <stdlib.h>
#include <inttypes.h>
/* Used only by Sensor Thread: no shared PRNG state. */
static SensorData simulated(unsigned *seed)
{
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC,&now);
    return (SensorData){(uint64_t)now.tv_sec*1000+now.tv_nsec/1000000,
        15.0+(rand_r(seed)%301)/10.0,30.0+(rand_r(seed)%601)/10.0};
}
void *sensor_thread(void *arg)
{
    App *a=arg;
    struct timespec expected,actual;
    unsigned seed=205068,iterations=0;
    int rc;
    if (!a->config.other) {
        struct sched_param sp={.sched_priority=SENSOR_PRIORITY};
        rc=pthread_setschedparam(pthread_self(),SCHED_FIFO,&sp);
        if (rc) { errno=rc; app_error(a,"pthread_setschedparam FIFO"); goto done; }
    }
    int policy;
    struct sched_param current;
    pthread_getschedparam(pthread_self(),&policy,&current);
    printf("SENSOR policy=%s priority=%d backend=%s\n",policy==SCHED_FIFO?"FIFO":"OTHER",current.sched_priority,a->config.simulate?"HOST_SIMULATOR":"ARM_DRIVER");
    app_log(a,"Sensor started policy=%d priority=%d",policy,current.sched_priority);
    clock_gettime(CLOCK_MONOTONIC,&expected);
    while (!atomic_load(&a->stop)) {
        SensorData d;
        expected.tv_sec+=a->config.interval_ms/1000;
        expected.tv_nsec+=(long)(a->config.interval_ms%1000)*1000000L;
        expected.tv_sec+=expected.tv_nsec/1000000000L;
        expected.tv_nsec%=1000000000L;
        do { rc=clock_nanosleep(CLOCK_MONOTONIC,TIMER_ABSTIME,&expected,NULL); }
        while (rc==EINTR && !atomic_load(&a->stop));
        if (atomic_load(&a->stop)) break;
        if (rc) { errno=rc; app_error(a,"clock_nanosleep"); break; }
        clock_gettime(CLOCK_MONOTONIC,&actual);
        if (a->jitter_count<JITTER_CAPACITY)
            a->jitter[a->jitter_count++]=timespec_diff_us(&actual,&expected);
        if (a->config.simulate) d=simulated(&seed);
        else {
            char line[128];
            if (lseek(a->fd,0,SEEK_SET)<0) { app_error(a,"sensor seek"); break; }
            ssize_t n=read(a->fd,line,sizeof(line)-1);
            if (n<0) {
                if (errno==EAGAIN || errno==EINTR) { app_log(a,"Sensor retry errno=%d",errno); goto next; }
                app_error(a,"sensor read"); break;
            }
            if (!n) { app_log(a,"Sensor EOF; retry next period"); goto next; }
            line[n]=0;
            if (sscanf(line,"%" SCNu64 ",%lf,%lf",&d.timestamp,&d.temperature,&d.humidity)!=3) {
                errno=EPROTO; app_error(a,"sensor CSV"); break;
            }
        }
        if (!buffer_push(&a->buffer,d)) app_log(a,"Sensor overflow: dropped sample");
        if (a->config.verbose) printf("SAMPLE %" PRIu64 " %.1f %.1f\n",d.timestamp,d.temperature,d.humidity);
next:
        if (++iterations==a->config.sample_limit && a->config.sample_limit) break;
    }
done:
    buffer_close(&a->buffer);
    atomic_store(&a->sensor_done,true);
    return NULL;
}
