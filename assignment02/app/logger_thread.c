/* Single-owner log file with timed flush and bounded rotation.
 * Mai The Tam - SE205068 - LOS201, 2026-11-07. */
#include "sms_app.h"
#include "logger_thread.h"
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
void *logger_thread(void *arg)
{
    App *a=arg;
    FILE *file=fopen(a->config.log_path,"a");
    if (!file) { app_error(a,"log fopen"); atomic_store(&a->logger_done,true); return NULL; }
    char rotated[4096];
    snprintf(rotated,sizeof(rotated),"%s.1",a->config.log_path);
    struct timespec flushed;
    clock_gettime(CLOCK_MONOTONIC,&flushed);
    fprintf(file,"Logger started\n");
    for (;;) {
        char message[MESSAGE_SIZE];
        struct timespec deadline=deadline_after_ms(100),now;
        ssize_t n=mq_timedreceive(a->logs,message,sizeof(message),NULL,&deadline);
        if (n>=0) {
            struct timespec realtime;
            struct tm tm;
            char stamp[64];
            clock_gettime(CLOCK_REALTIME,&realtime);
            localtime_r(&realtime.tv_sec,&tm);
            strftime(stamp,sizeof(stamp),"%Y-%m-%dT%H:%M:%S",&tm);
            if (fprintf(file,"%s.%03ld %.*s\n",stamp,realtime.tv_nsec/1000000,(int)n,message)<0) {
                app_error(a,"log fprintf"); break;
            }
            long size=ftell(file);
            if (size<0) { app_error(a,"log ftell"); break; }
            if (size>1024*1024) {
                if (fclose(file)) { file=NULL; app_error(a,"log close rotate"); break; }
                file=NULL;
                if (rename(a->config.log_path,rotated)) { app_error(a,"log rename"); break; }
                file=fopen(a->config.log_path,"w");
                if (!file) { app_error(a,"log reopen"); break; }
            }
        } else if (errno!=EINTR && errno!=ETIMEDOUT) { app_error(a,"log mq_receive"); break; }
        else if (errno==ETIMEDOUT && atomic_load(&a->alert_done)) break;
        clock_gettime(CLOCK_MONOTONIC,&now);
        if (now.tv_sec-flushed.tv_sec>=5) {
            if (fflush(file)) { app_error(a,"log fflush"); break; }
            flushed=now;
        }
    }
    if (file && fclose(file)) app_error(a,"log final close");
    atomic_store(&a->logger_done,true);
    return NULL;
}
