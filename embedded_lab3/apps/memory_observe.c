#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* Same workload as the original app, with explicit observation windows. */
typedef struct { int id; char *name; int *scores; } Record;

static int workload(int fixed)
{
    Record **records = calloc(100, sizeof(*records));
    if (!records) return -1;
    for (int i = 0; i < 100; i++) {
        records[i] = calloc(1, sizeof(**records));
        if (!records[i]) goto fail;
        records[i]->name = strdup("EmbeddedLinuxStudent");
        records[i]->scores = malloc(5 * sizeof(int));
        if (!records[i]->name || !records[i]->scores) goto fail;
        records[i]->id = i;
        for (int j = 0; j < 5; j++) records[i]->scores[j] = i * 10 + j;
    }
    for (int i = 0; i < 100; i++) {
        if (fixed) { free(records[i]->name); free(records[i]->scores); }
        free(records[i]);
    }
    free(records);
    for (int i = 0; i < 50; i++) {
        char *buf = malloc(256);
        if (!buf) return -1;
        snprintf(buf, 256, "Message #%d: data payload here", i);
        if (i % 10 == 0) printf("Processed: %s\n", buf);
        if (fixed) free(buf);
    }
    return 0;
fail:
    for (int i = 0; i < 100; i++) {
        if (records[i]) { free(records[i]->name); free(records[i]->scores); free(records[i]); }
    }
    free(records);
    return -1;
}

int main(int argc, char **argv)
{
    int fixed = argc == 2 && strcmp(argv[1], "fixed") == 0;
    if (argc != 2 || (!fixed && strcmp(argv[1], "leaky") != 0)) {
        fprintf(stderr, "Usage: %s leaky|fixed\n", argv[0]);
        return 2;
    }
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("PID=%ld MODE=%s PHASE=before\n", (long)getpid(), argv[1]);
    sleep(5);
    if (workload(fixed) != 0) return 1;
    printf("PID=%ld MODE=%s PHASE=after\n", (long)getpid(), argv[1]);
    sleep(8);
    return 0;
}
