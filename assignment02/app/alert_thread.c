/* POSIX MQ alarm consumer. Mai The Tam - SE205068, 2026-11-07. */
#include "sms_app.h"
#include "alert_thread.h"
#include <stdio.h>
#include <inttypes.h>
#include <errno.h>
void *alert_thread(void *arg)
{
    App *a=arg;
    const char *types[]={"TEMP_HIGH","HUMID_HIGH","TEMP_SPIKE"};
    app_log(a,"Alert started");
    for (;;) {
        Alarm alarm;
        struct timespec deadline=deadline_after_ms(100);
        ssize_t n=mq_timedreceive(a->alarms,(char *)&alarm,sizeof(alarm),NULL,&deadline);
        if (n<0) {
            if (errno==EINTR) continue;
            if (errno==ETIMEDOUT) { if (atomic_load(&a->processor_done)) break; continue; }
            app_error(a,"alarm mq_receive"); break;
        }
        if (n!=(ssize_t)sizeof(alarm) || alarm.type<0 || alarm.type>2) {
            errno=EPROTO; app_error(a,"alarm message"); break;
        }
        a->alert_counts[alarm.type]++;
        fprintf(stderr,"[ALERT][%" PRIu64 "] TYPE: %s VALUE: %.1f THRESHOLD: %.1f\n",
                alarm.timestamp,types[alarm.type],alarm.value,alarm.threshold);
        app_log(a,"Alert TYPE=%s VALUE=%.1f THRESHOLD=%.1f",types[alarm.type],alarm.value,alarm.threshold);
    }
    atomic_store(&a->alert_done,true);
    return NULL;
}
