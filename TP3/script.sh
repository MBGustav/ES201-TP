#!/bin/bash
set -e

GEM5=/home/higepi/gem5/build/RISCV/gem5.opt
CFG=/home/higepi/TP/se_fu.py

for N in min med max; do
  BIN="pagerank_${N}.riscv"
  for M in 1 2 4 8; do
    OUT="m5out_${N}_M${M}"
    $GEM5 -d "$OUT" "$CFG" \
      --cmd="./$BIN" \
      --cpu-type=O3 --caches \
      --ialu=$M --imult=$M --fpalu=1 --fpmult=1 --memport=2
  done
done
