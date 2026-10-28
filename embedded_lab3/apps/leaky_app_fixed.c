#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NUM_RECORDS 100
#define MSG_SIZE 256

typedef struct {
    int id;
    char *name;
    int *scores;
} Record;

/* A record owns its nested allocations until delete_record releases them. */
static void delete_record(Record *r)
{
    if (!r) return;
    free(r->name);
    free(r->scores);
    free(r);
}

static Record *create_record(int id, const char *name, int num_scores)
{
    Record *r = calloc(1, sizeof(*r));
    if (!r) return NULL;
    r->id = id;
    r->name = malloc(strlen(name) + 1);
    r->scores = malloc(sizeof(*r->scores) * (size_t)num_scores);
    if (!r->name || !r->scores) {
        delete_record(r);
        return NULL;
    }
    strcpy(r->name, name);
    for (int i = 0; i < num_scores; i++) r->scores[i] = id * 10 + i;
    return r;
}

static int process_messages(int count)
{
    for (int i = 0; i < count; i++) {
        char *buf = malloc(MSG_SIZE);
        if (!buf) return -1;
        snprintf(buf, MSG_SIZE, "Message #%d: data payload here", i);
        if (i % 10 == 0) printf("  Processed: %s\n", buf);
        free(buf);
    }
    return 0;
}

int main(void)
{
    int created = 0;
    Record **records = calloc(NUM_RECORDS, sizeof(*records));
    if (!records) return EXIT_FAILURE;
    for (; created < NUM_RECORDS; created++) {
        records[created] = create_record(created, "EmbeddedLinuxStudent", 5);
        if (!records[created]) break;
    }
    for (int i = 0; i < created; i++) delete_record(records[i]);
    free(records);
    if (created != NUM_RECORDS || process_messages(50) != 0) {
        fputs("Allocation failed\n", stderr);
        return EXIT_FAILURE;
    }
    puts("Fixed workload finished");
    return EXIT_SUCCESS;
}
