/* SMS lifecycle, CLI, queues, and jitter report.
 * Mai The Tam - SE205068 - LOS201, 2026-11-07. */
#include "sms_app.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>
#include <signal.h>
#include <errno.h>
#include <stdarg.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <math.h>
static volatile sig_atomic_t interrupted;
static void on_signal(int sig) { (void)sig; interrupted=1; }
int64_t timespec_diff_us(const struct timespec *a,const struct timespec *b)
{
    return (int64_t)(a->tv_sec-b->tv_sec)*1000000LL+(a->tv_nsec-b->tv_nsec)/1000;
}
struct timespec deadline_after_ms(unsigned ms)
{
    struct timespec t;
    clock_gettime(CLOCK_REALTIME,&t);
    t.tv_nsec+=(long)ms*1000000L;
    t.tv_sec+=t.tv_nsec/1000000000L;
    t.tv_nsec%=1000000000L;
    return t;
}
void app_error(App *a,const char *operation)
{
    fprintf(stderr,"ERROR %s: %s\n",operation,strerror(errno));
    atomic_store(&a->failed,1);
    atomic_store(&a->stop,true);
}
int app_log(App *a,const char *format,...)
{
    char message[MESSAGE_SIZE];
    va_list ap;
    va_start(ap,format); vsnprintf(message,sizeof(message),format,ap); va_end(ap);
    while (!atomic_load(&a->logger_done)) {
        struct timespec deadline=deadline_after_ms(100);
        if (!mq_timedsend(a->logs,message,strlen(message),0,&deadline)) return 0;
        if (errno!=EINTR && errno!=ETIMEDOUT) break;
    }
    app_error(a,"log mq_send");
    return -1;
}
static int compare_long(const void *x,const void *y)
{
    long a=*(const long *)x,b=*(const long *)y;
    return (a>b)-(a<b);
}
static int jitter_report(App *a)
{
    FILE *f=a->config.jitter_path?fopen(a->config.jitter_path,"w"):stdout;
    if (!f) return -1;
    size_t n=a->jitter_count,bins[4]={0};
    long double sum=0;
    for (size_t i=0;i<n;i++) {
        long j=a->jitter[i]; sum+=j;
        bins[j<100?0:j<500?1:j<1000?2:3]++;
    }
    qsort(a->jitter,n,sizeof(long),compare_long);
    size_t p99=n?(99*n+99)/100-1:0;
    fprintf(f,"backend=%s policy=%s interval_ms=%u samples=%zu\n",a->config.simulate?"HOST_SIMULATOR":"ARM_DRIVER",a->config.other?"OTHER":"FIFO",a->config.interval_ms,n);
    if (n) fprintf(f,"min_us=%ld avg_us=%.3Lf max_us=%ld p99_us=%ld\n",a->jitter[0],sum/n,a->jitter[n-1],a->jitter[p99]);
    fprintf(f,"[0,100)us=%zu [100,500)us=%zu [500,1000)us=%zu [1000,+inf)us=%zu\n",bins[0],bins[1],bins[2],bins[3]);
    int error=ferror(f);
    if (f!=stdout && fclose(f)) error=1;
    return error?-1:0;
}
static unsigned number(const char *s,unsigned max)
{
    char *end;
    errno=0;
    unsigned long v=strtoul(s,&end,10);
    if (errno || !*s || *end || *s=='-' || v>max) { fprintf(stderr,"Invalid number: %s\n",s); exit(2); }
    return (unsigned)v;
}
static double threshold(const char *s)
{
    char *end;
    errno=0;
    double v=strtod(s,&end);
    if (errno || !*s || *end || !isfinite(v)) { fprintf(stderr,"Invalid threshold: %s\n",s); exit(2); }
    return v;
}
static void usage(void)
{
    puts("sms_app [-i ms] [-t Celsius] [-h percent] [-d seconds] [-v]\n"
         "  --other --simulate --samples N --device PATH --log PATH --jitter PATH\n"
         "  defaults: interval=500, temp=40, humid=80, duration=60, FIFO priority=50\n"
         "  --simulate is a HOST test backend; it does not exercise the kernel driver.");
}
int main(int argc,char **argv)
{
    App a={.config={.interval_ms=500,.duration=60,.temp_threshold=40,.humidity_threshold=80,
        .device=SMS_DEVICE_PATH,.log_path=SMS_LOG_PATH},.alarms=(mqd_t)-1,.logs=(mqd_t)-1,.fd=-1};
    struct option options[]={
        {"other",0,NULL,1000},{"simulate",0,NULL,1001},{"samples",1,NULL,1002},
        {"device",1,NULL,1003},{"log",1,NULL,1004},{"jitter",1,NULL,1005},{"help",0,NULL,1006},{NULL,0,NULL,0}};
    int opt,rc=1,started=0;
    while ((opt=getopt_long(argc,argv,"i:t:h:d:v",options,NULL))!=-1) {
        switch(opt) {
        case 'i': a.config.interval_ms=number(optarg,60000); if(!a.config.interval_ms) return 2; break;
        case 't': a.config.temp_threshold=threshold(optarg); break;
        case 'h': a.config.humidity_threshold=threshold(optarg); break;
        case 'd': a.config.duration=number(optarg,86400); break;
        case 'v': a.config.verbose=true; break;
        case 1000: a.config.other=true; break;
        case 1001: a.config.simulate=true; break;
        case 1002: a.config.sample_limit=number(optarg,JITTER_CAPACITY); break;
        case 1003: a.config.device=optarg; break;
        case 1004: a.config.log_path=optarg; break;
        case 1005: a.config.jitter_path=optarg; break;
        case 1006: usage(); return 0;
        default: usage(); return 2;
        }
    }
    if (optind!=argc) { usage(); return 2; }
    signal(SIGINT,on_signal); signal(SIGTERM,on_signal);
    setvbuf(stdout,NULL,_IOLBF,0);
    atomic_init(&a.stop,false); atomic_init(&a.failed,0);
    atomic_init(&a.sensor_done,false); atomic_init(&a.processor_done,false);
    atomic_init(&a.alert_done,false); atomic_init(&a.logger_done,false);
    if (buffer_init(&a.buffer,64)) { perror("buffer_init"); return 1; }
    a.jitter=calloc(JITTER_CAPACITY,sizeof(long));
    if (!a.jitter) { perror("jitter calloc"); goto cleanup_buffer; }
    if (!a.config.simulate) {
        a.fd=open(a.config.device,O_RDONLY|O_CLOEXEC);
        if (a.fd<0) { perror("sensor open"); goto cleanup; }
        if (ioctl(a.fd,SMS_SET_INTERVAL,&a.config.interval_ms)) { perror("sensor ioctl"); goto cleanup; }
    }
    char alarm_name[64],log_name[64];
    snprintf(alarm_name,sizeof(alarm_name),"/sms_alarm_%ld",(long)getpid());
    snprintf(log_name,sizeof(log_name),"/sms_log_%ld",(long)getpid());
    struct mq_attr attr={.mq_maxmsg=10,.mq_msgsize=sizeof(Alarm)};
    a.alarms=mq_open(alarm_name,O_CREAT|O_EXCL|O_RDWR,0600,&attr);
    if (a.alarms==(mqd_t)-1) { perror("alarm mq_open"); goto cleanup; }
    mq_unlink(alarm_name);
    attr.mq_msgsize=MESSAGE_SIZE;
    a.logs=mq_open(log_name,O_CREAT|O_EXCL|O_RDWR,0600,&attr);
    if (a.logs==(mqd_t)-1) { perror("log mq_open"); goto cleanup; }
    mq_unlink(log_name);
    if (mlockall(MCL_CURRENT|MCL_FUTURE)) {
        if (!a.config.other) { perror("mlockall"); goto cleanup; }
        fprintf(stderr,"mlockall unavailable in OTHER run: %s\n",strerror(errno));
    }
    pthread_attr_t thread_attr;
    pthread_attr_init(&thread_attr);
    pthread_attr_setstacksize(&thread_attr,SENSOR_STACK);
    pthread_t threads[4];
    void *(*functions[])(void *)={logger_thread,alert_thread,processor_thread,sensor_thread};
    struct timespec begin,now;
    clock_gettime(CLOCK_MONOTONIC,&begin);
    puts("STATE INIT -> RUNNING");
    for (started=0;started<4;started++) {
        int err=pthread_create(&threads[started],&thread_attr,functions[started],&a);
        if (err) { errno=err; app_error(&a,"pthread_create"); break; }
    }
    pthread_attr_destroy(&thread_attr);
    while (started==4 && !atomic_load(&a.stop) && !atomic_load(&a.sensor_done) && !interrupted) {
        clock_gettime(CLOCK_MONOTONIC,&now);
        if (a.config.duration && timespec_diff_us(&now,&begin)>=(int64_t)a.config.duration*1000000LL) break;
        struct timespec wait={0,50000000}; nanosleep(&wait,NULL);
    }
    puts("STATE RUNNING -> SHUTDOWN");
    atomic_store(&a.stop,true);
    if (started<4) { buffer_close(&a.buffer); atomic_store(&a.sensor_done,true); }
    if (started<3) atomic_store(&a.processor_done,true);
    if (started<2) atomic_store(&a.alert_done,true);
    /* Join producer to consumer so every accepted message drains before exit. */
    for (int i=started-1;i>=0;i--) pthread_join(threads[i],NULL);
    clock_gettime(CLOCK_MONOTONIC,&now);
    BufferStats s=buffer_stats(&a.buffer);
    printf("SUMMARY produced=%lu consumed=%lu overflow=%lu current=%zu TEMP_HIGH=%lu HUMID_HIGH=%lu TEMP_SPIKE=%lu uptime=%.3f\n",
            s.total_produced,s.total_consumed,s.overflow_count,s.current_size,
            a.alert_counts[0],a.alert_counts[1],a.alert_counts[2],timespec_diff_us(&now,&begin)/1000000.0);
    if (jitter_report(&a)) { perror("jitter report"); atomic_store(&a.failed,1); }
    rc=atomic_load(&a.failed)?1:0;
cleanup:
    munlockall();
    if (a.fd>=0) close(a.fd);
    if (a.alarms!=(mqd_t)-1) mq_close(a.alarms);
    if (a.logs!=(mqd_t)-1) mq_close(a.logs);
    free(a.jitter);
cleanup_buffer:
    buffer_destroy(&a.buffer);
    return rc;
}
