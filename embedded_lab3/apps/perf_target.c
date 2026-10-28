#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <unistd.h>

#define ARRAY_SIZE  100000
#define ITERATIONS  50

/* Hàm tính toán nặng – CPU bound */
double heavy_compute(double *arr, int n) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += sqrt(arr[i]) * log(arr[i] + 1.0);
    }
    return result;
}

/* Hàm tìm kiếm tuyến tính – O(n) */
int linear_search(int *arr, int n, int target) {
    for (int i = 0; i < n; i++)
        if (arr[i] == target) return i;
    return -1;
}

/* Hàm I/O – nhiều system call */
int io_intensive(int count) {
    char path[] = "/tmp/los201-perf-XXXXXX";
    int fd = mkstemp(path);
    if (fd < 0) { perror("mkstemp"); return -1; }
    FILE *f = fdopen(fd, "w");
    if (!f) { perror("fdopen"); close(fd); unlink(path); return -1; }
    for (int i = 0; i < count; i++) {
        if (fprintf(f, "Line %d: measurement data\n", i) < 0) {
            fclose(f); unlink(path); return -1;
        }
    }
    int result = fclose(f);
    unlink(path);
    return result;
}

int main(int argc, char **argv) {
    int iterations = ITERATIONS;
    if (argc == 2) {
        char *end;
        long value = strtol(argv[1], &end, 10);
        if (*end || value < 1 || value > 10000) return 2;
        iterations = (int)value;
    } else if (argc != 1) return 2;
    printf("=== Perf Target App – LAB-03 ===\n");

    /* Khởi tạo array */
    double *darr = malloc(sizeof(double) * ARRAY_SIZE);
    int    *iarr = malloc(sizeof(int)    * ARRAY_SIZE);
    if (!darr || !iarr) { free(darr); free(iarr); return 1; }
    for (int i = 0; i < ARRAY_SIZE; i++) {
        darr[i] = (double)(i + 1);
        iarr[i] = i;
    }

    printf("[1] CPU-intensive computation...\n");
    double total = 0;
    for (int iter = 0; iter < iterations; iter++)
        total += heavy_compute(darr, ARRAY_SIZE);
    printf("    Result: %f\n", total);

    printf("[2] Linear search (1000 times)...\n");
    int search_checksum = 0;
    for (int i = 0; i < 1000; i++)
        /* Vary the query so the compiler cannot hoist one pure search. */
        search_checksum += linear_search(iarr, ARRAY_SIZE, ARRAY_SIZE - 1 - i % 17);
    printf("    Search checksum: %d\n", search_checksum);

    printf("[3] I/O intensive (write 10000 lines)...\n");
    int io_result = io_intensive(10000);

    free(darr); free(iarr);
    printf("Done.\n");
    return io_result == 0 ? 0 : 1;
}
