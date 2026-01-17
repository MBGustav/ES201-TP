#!/bin/bash
set -e

GEM5="$HOME/gem5/build/RISCV/gem5.opt"
CFG="$HOME/ES201-TP/se_fu.py"
BASE="$HOME/ES201-TP/TP3/PageRank"

for N in min med max; do
  BIN="$BASE/pagerank_${N}.riscv"

  # In-order
  $GEM5 -d "m5out_${N}_inorder" "$CFG" \
    --cmd="$BIN" --cpu-type=TimingSimpleCPU --caches

  # Out-of-order
  $GEM5 -d "m5out_${N}_ooo" "$CFG" \
    --cmd="$BIN" --cpu-type=O3 --caches \
    --ialu=4 --imult=4 --fpalu=1 --fpmult=1 --memport=2
done

for d in m5out_*_inorder m5out_*_ooo; do
  [ -f "$d/stats.txt" ] || continue
  C=$(grep -m1 "system.cpu.numCycles" "$d/stats.txt" | awk '{print $2}')
  CPI=$(grep -m1 "system.cpu.cpi" "$d/stats.txt" | awk '{print $2}')
  echo "$d cycles=$C cpi=$CPI"
done

