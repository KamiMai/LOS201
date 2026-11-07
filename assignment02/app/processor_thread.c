/* Rolling window and alarm decisions. Mai The Tam - SE205068, 2026-11-07. */
#include "sms_app.h"
#include "processor_thread.h"
#include <math.h>
#include <stdio.h>
#include <inttypes.h>
#include <errno.h>
/* Keep this function separate for GDB's alert-injection experiment. */
static void detect_alert(App *a, SensorData sample, double previous, bool have_previous)
{
    Alarm alarms[3];
    size_t count=0;
    double temperature=sample.temperature;
    if (temperature>a->config.temp_threshold)
        alarms[count++]=(Alarm){sample.timestamp,0,temperature,a->config.temp_threshold};
    if (sample.humidity>a->config.humidity_threshold)
        alarms[count++]=(Alarm){sample.timestamp,1,sample.humidity,a->config.humidity_threshold};
    if (have_previous && fabs(temperature-previous)>5.0)
        alarms[count++]=(Alarm){sample.timestamp,2,fabs(temperature-previous),5.0};
    for (size_t i=0;i<count;i++) {
        while (mq_send(a->alarms,(const char *)&alarms[i],sizeof(Alarm),0)<0) {
            if (errno==EINTR) continue;
            app_error(a,"alarm mq_send"); return;
        }
    }
}
void *processor_thread(void *arg)
{
    App *a=arg;
    SensorData sample,window[10];
    size_t index=0,size=0;
    double sum_t=0,sum_h=0,previous=0;
    bool have_previous=false;
    app_log(a,"Processor started");
    while (buffer_pop(&a->buffer,&sample)) {
        if (size==10) { sum_t-=window[index].temperature; sum_h-=window[index].humidity; }
        else size++;
        window[index]=sample; index=(index+1)%10;
        sum_t+=sample.temperature; sum_h+=sample.humidity;
        detect_alert(a,sample,previous,have_previous);
        previous=sample.temperature; have_previous=true;
        app_log(a,"Processor sample=%" PRIu64 " temp=%.1f humid=%.1f rolling_temp=%.3f rolling_humid=%.3f n=%zu",
                sample.timestamp,sample.temperature,sample.humidity,sum_t/size,sum_h/size,size);
    }
    atomic_store(&a->processor_done,true);
    return NULL;
}
