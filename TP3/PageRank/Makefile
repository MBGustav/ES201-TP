CC_HOST=gcc
CC_RISCV=riscv64-linux-gnu-gcc

CFLAGS_COMMON=-std=c99 -O2 -g3 -lm
CFLAGS_RISCV=-static -O2 -g3 -std=c99

all: pagerank pagerank_min.riscv pagerank_med.riscv pagerank_max.riscv

# binaire natif (host) pour debug rapide
pagerank: main.c examples.h
	$(CC_HOST) main.c -o pagerank $(CFLAGS_COMMON) -D_MAT_TWITTER

# binaires RISC-V pour gem5 (SE)
pagerank_med.riscv: main.c examples.h
	$(CC_RISCV) main.c -o pagerank_med.riscv $(CFLAGS_RISCV) -D_MAT_SIMPLE -lm

pagerank_max.riscv: main.c examples.h
	$(CC_RISCV) main.c -o pagerank_max.riscv $(CFLAGS_RISCV) -D_MAT_TWITTER -lm

pagerank_min.riscv: main.c examples.h
	$(CC_RISCV) main.c -o pagerank_min.riscv $(CFLAGS_RISCV) -D_MAT_EXAMPLE3 -lm

clean:
	rm -f pagerank pagerank_*.riscv
