CC ?= gcc
CROSS_COMPILE ?= arm-linux-gnueabihf-
CFLAGS := -std=c11 -g3 -O0 -Wall -Wextra -Werror -fno-omit-frame-pointer
SOURCES := sms_app.c sensor_thread.c processor_thread.c alert_thread.c logger_thread.c circular_buffer.c
LDLIBS := -pthread -lrt -lm
.PHONY: all host arm clean
all: host arm
host: sms_app_x86
arm: sms_app
sms_app_x86: $(SOURCES) $(wildcard *.h) ../driver/sms_sensor.h
	$(CC) $(CFLAGS) -o $@ $(SOURCES) $(LDLIBS)
sms_app: $(SOURCES) $(wildcard *.h) ../driver/sms_sensor.h
	$(CROSS_COMPILE)gcc $(CFLAGS) -march=armv7-a -mfpu=neon -mfloat-abi=hard -o $@ $(SOURCES) $(LDLIBS)
clean:
	rm -f sms_app sms_app_x86
