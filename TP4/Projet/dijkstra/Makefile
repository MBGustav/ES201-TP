# Makefile

# ---------- TOOLCHAIN ----------
# ARM 
CC = arm-linux-gnueabihf-gcc

CFLAGS = -O3 -static -Wall -std=c99

all: dijkstra_large.arm dijkstra_small.arm

dijkstra_large.arm: dijkstra_large.c Makefile
	$(CC) $(CFLAGS) dijkstra_large.c -o dijkstra_large.arm

dijkstra_small.arm: dijkstra_small.c Makefile
	$(CC) $(CFLAGS) dijkstra_small.c -o dijkstra_small.arm

clean:
	rm -f dijkstra_large.arm dijkstra_small.arm *.o
	rm -rf m5out_* output*
