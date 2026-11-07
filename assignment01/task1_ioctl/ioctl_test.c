/* Userspace ABI and error tests. Mai The Tam - SE205068, 2026-11-07. */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include "asgn1_ioctl.h"
#define CHECK(c) do { if (!(c)) { fprintf(stderr, "FAIL line %d: %s errno=%d\n", __LINE__, #c, errno); exit(1); } } while (0)
/* read_back: open a fresh file description and assert exact expected data; no return. */
static void read_back(const char *expected)
{
    char buf[1200] = {0};
    int fd = open("/dev/asgn1", O_RDONLY);
    CHECK(fd >= 0);
    ssize_t n = read(fd, buf, sizeof(buf)-1);
    CHECK(n >= 0 && (size_t)n == strlen(expected) && !strcmp(buf, expected));
    CHECK(read(fd, buf, sizeof(buf)) == 0);
    CHECK(close(fd) == 0);
    printf("read verified: [%s]\n", expected);
}
/* main: exercise all four commands and negative cases; return success or failure. */
int main(void)
{
    struct asgn1_stats s;
    char version[64];
    int mode = 0, fd = open("/dev/asgn1", O_RDWR);
    CHECK(fd >= 0);
    CHECK(write(fd, "echo", 4) == 4);
    read_back("echo");
    CHECK(ioctl(fd, ASGN1_SET_MODE, &mode) == 0);
    CHECK(write(fd, "test", 4) == 4);
    read_back("[KERNEL]test");
    CHECK(ioctl(fd, ASGN1_GET_STATS, &s) == 0);
    printf("open_count=%d write_count=%d read_count=%d buffer_len=%d last_write_size=%d\n", s.open_count,s.write_count,s.read_count,s.buffer_len,s.last_write_size);
    CHECK(s.open_count == 3 && s.write_count == 2 && s.read_count == 2 && s.buffer_len == 12 && s.last_write_size == 4);
    memset(version, 0x55, sizeof(version));
    CHECK(ioctl(fd, ASGN1_GET_VERSION, version) == 0);
    CHECK(memchr(version, 0, sizeof(version)) != NULL);
    printf("version=%s; stats_size=%u cmd=0x%lx\n", version, (unsigned)_IOC_SIZE(ASGN1_GET_STATS), (unsigned long)ASGN1_GET_STATS);
    mode = 2;
    CHECK(ioctl(fd, ASGN1_SET_MODE, &mode) == -1 && errno == EINVAL);
    CHECK(ioctl(fd, _IO(ASGN1_MAGIC,99)) == -1 && errno == ENOTTY);
    CHECK(ioctl(fd, ASGN1_GET_STATS, NULL) == -1 && errno == EFAULT);
    CHECK(ioctl(fd, ASGN1_RESET_BUFFER) == 0);
    CHECK(ioctl(fd, ASGN1_GET_STATS, &s) == 0);
    CHECK(s.write_count == 0 && s.read_count == 0 && s.buffer_len == 0);
    read_back("");
    mode = 1;
    CHECK(ioctl(fd, ASGN1_SET_MODE, &mode) == 0);
    CHECK(close(fd) == 0);
    puts("IOCTL TEST PASSED");
    return 0;
}
