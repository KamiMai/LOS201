CC = gcc
ARM_CC = arm-linux-gnueabihf-gcc
ARM_FLAGS = -marm -march=armv7-a -mfpu=neon -mfloat-abi=hard -static
DEBUG_FLAGS = -g -O0
PROFILE_FLAGS = -g -O1 -fno-omit-frame-pointer

buggy_app: buggy_app.c
	$(ARM_CC) $(DEBUG_FLAGS) $(ARM_FLAGS) -o $@ $<

leaky_app: leaky_app.c
	$(CC) $(DEBUG_FLAGS) -o $@ $<

perf_target: perf_target.c
	$(CC) $(PROFILE_FLAGS) -o $@ $< -lm

perf_target_arm: perf_target.c
	$(ARM_CC) $(PROFILE_FLAGS) $(ARM_FLAGS) -o $@ $< -lm
