#ifndef CIRCULAR_BUFFER_H
#define CIRCULAR_BUFFER_H
#include <pthread.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef struct { uint64_t timestamp; double temperature, humidity; } SensorData;
typedef struct {
    pthread_mutex_t mutex;
    pthread_cond_t available;
    SensorData *items;
    size_t head, tail, size, capacity;
    unsigned long produced, consumed, overflow;
    bool closed;
} CircularBuffer;
typedef struct { size_t current_size; unsigned long total_produced,total_consumed,overflow_count; } BufferStats;
int buffer_init(CircularBuffer *, size_t);
void buffer_destroy(CircularBuffer *);
bool buffer_push(CircularBuffer *, SensorData);
bool buffer_pop(CircularBuffer *, SensorData *);
void buffer_close(CircularBuffer *);
BufferStats buffer_stats(CircularBuffer *);
#endif
