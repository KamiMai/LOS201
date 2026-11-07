/* Bounded single-producer/single-consumer storage.
 * Mai The Tam - SE205068 - LOS201, 2026-11-07. */
#include "circular_buffer.h"
#include <stdlib.h>
int buffer_init(CircularBuffer *b, size_t capacity)
{
    *b = (CircularBuffer){0};
    b->items = calloc(capacity, sizeof(*b->items));
    if (!b->items) return -1;
    if (pthread_mutex_init(&b->mutex,NULL)) { free(b->items); return -1; }
    if (pthread_cond_init(&b->available,NULL)) {
        pthread_mutex_destroy(&b->mutex); free(b->items); return -1;
    }
    b->capacity=capacity;
    return 0;
}
void buffer_destroy(CircularBuffer *b)
{
    pthread_cond_destroy(&b->available);
    pthread_mutex_destroy(&b->mutex);
    free(b->items);
}
bool buffer_push(CircularBuffer *b, SensorData d)
{
    bool ok=false;
    pthread_mutex_lock(&b->mutex);
    if (!b->closed && b->size < b->capacity) {
        b->items[b->head]=d;
        b->head=(b->head+1)%b->capacity;
        b->size++; b->produced++; ok=true;
        pthread_cond_signal(&b->available);
    } else if (!b->closed) b->overflow++;
    pthread_mutex_unlock(&b->mutex);
    return ok;
}
bool buffer_pop(CircularBuffer *b, SensorData *d)
{
    pthread_mutex_lock(&b->mutex);
    while (!b->size && !b->closed) pthread_cond_wait(&b->available,&b->mutex);
    if (!b->size) { pthread_mutex_unlock(&b->mutex); return false; }
    *d=b->items[b->tail];
    b->tail=(b->tail+1)%b->capacity;
    b->size--; b->consumed++;
    pthread_mutex_unlock(&b->mutex);
    return true;
}
void buffer_close(CircularBuffer *b)
{
    pthread_mutex_lock(&b->mutex);
    b->closed=true;
    pthread_cond_broadcast(&b->available);
    pthread_mutex_unlock(&b->mutex);
}
BufferStats buffer_stats(CircularBuffer *b)
{
    BufferStats s;
    pthread_mutex_lock(&b->mutex);
    s=(BufferStats){b->size,b->produced,b->consumed,b->overflow};
    pthread_mutex_unlock(&b->mutex);
    return s;
}
