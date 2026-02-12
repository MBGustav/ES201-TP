#!/bin/bash
set -e

# Q4/Q5 sweep script
# Usage:
#   ./run_q45.sh
#   ./run_q45.sh a7
#   ./run_q45.sh a15
#   ./run_q45.sh both /path/to/gem5.opt

ARCH_MODE="${1:-both}"  # a7 | a15 | both
GEM5="${2:-${GEM5:-$HOME/Projects/architecture-microprocesseurs/gem5/build/RISCV/gem5.opt}}"

if [ "$ARCH_MODE" != "a7" ] && [ "$ARCH_MODE" != "a15" ] && [ "$ARCH_MODE" != "both" ]; then
  echo "Error: first arg must be a7, a15 or both"
  exit 1
fi

if [ ! -x "$GEM5" ]; then
  echo "Error: gem5 not found: $GEM5"
  exit 1
fi

BASE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$BASE/../.." && pwd)"

DIJ_DIR="$BASE/dijkstra"
BF_DIR="$BASE/blowfish"
DIJ_LARGE_BIN="$DIJ_DIR/dijkstra_large.riscv"
DIJ_INPUT="$DIJ_DIR/input.dat"
BF_BIN="$BF_DIR/bf.riscv"
BF_INPUT_LARGE="$BF_DIR/input_large.asc"
BF_KEY="0123456789ABCDEF"

CFG_A7="$ROOT/TP4/se_A7.py"
CFG_A15="$ROOT/TP4/se_A15.py"

OUT="$BASE/q45_m5out"
CSV="$OUT/q45_summary.csv"
CMDS="$OUT/q45_commands.sh"
mkdir -p "$OUT"

echo "== Configurations =="
echo "Q4 A7:  L1I=L1D in {1,2,4,8,16}kB, L2 fixed=512kB"
echo "Q5 A15: L1I=L1D in {2,4,8,16,32}kB, L2 fixed=512kB"
echo "Workloads:"
echo "  - dijkstra_large (input.dat)"
echo "  - blowfish (input_large.asc)"
echo

echo "== Building benchmarks =="
make -C "$DIJ_DIR" clean all
make -C "$BF_DIR" clean all

if [ ! -f "$DIJ_LARGE_BIN" ] || [ ! -f "$BF_BIN" ] || [ ! -f "$BF_INPUT_LARGE" ]; then
  echo "Error: missing binaries after build."
  exit 1
fi

echo "#!/bin/bash" > "$CMDS"
echo "set -e" >> "$CMDS"
echo "arch,question,workload,l1_kB,simSeconds,simInsts,numCycles,ipc,cpi,icache_miss,dcache_miss,l2_miss,bp_condPred,bp_condIncorrect,bp_condMispredRate,commit_branchMispredicts,outdir" > "$CSV"

get_stat() {
  local stats_file="$1"
  local key="$2"
  awk -v k="$key" '$1 == k {print $2; found=1; exit} END {if (!found) print "NA"}' "$stats_file"
}

get_stat_any() {
  local stats_file="$1"
  shift
  local value
  for key in "$@"; do
    value="$(get_stat "$stats_file" "$key")"
    if [ "$value" != "NA" ]; then
      echo "$value"
      return
    fi
  done
  echo "NA"
}

calc_ratio() {
  local num="$1"
  local den="$2"
  awk -v n="$num" -v d="$den" 'BEGIN {
    if (n == "NA" || d == "NA" || (d + 0) == 0) print "NA";
    else printf "%.6f", (n + 0) / (d + 0);
  }'
}

run_one() {
  local arch="$1"      # a7|a15
  local question="$2"  # Q4|Q5
  local cfg="$3"
  local size_kb="$4"
  local workload="$5"  # dijkstra_large|blowfish_large

  local l1_size="${size_kb}kB"
  local outdir="$OUT/m5out_${question}_${arch}_${workload}_l1_${size_kb}kB"
  local cmd

  if [ "$workload" = "dijkstra_large" ]; then
    cmd=( "$GEM5" -d "$outdir" "$cfg" --cmd "$DIJ_LARGE_BIN" --l1i-size "$l1_size" --l1d-size "$l1_size" --options "$DIJ_INPUT" )
  elif [ "$workload" = "blowfish_large" ]; then
    cmd=( "$GEM5" -d "$outdir" "$cfg" --cmd "$BF_BIN" --l1i-size "$l1_size" --l1d-size "$l1_size" --options e "$BF_INPUT_LARGE" "$outdir/output.enc" "$BF_KEY" )
  else
    echo "Error: unknown workload '$workload'"
    exit 1
  fi

  echo "== Running $question | $arch | $workload | L1=${size_kb}kB =="
  rm -rf "$outdir"

  printf "%q " "${cmd[@]}" >> "$CMDS"
  echo >> "$CMDS"

  "${cmd[@]}"

  local stats="$outdir/stats.txt"
  if [ ! -f "$stats" ]; then
    echo "Warning: stats.txt missing in $outdir"
    return
  fi

  local simSeconds simInsts numCycles ipc cpi
  local iMiss dMiss l2Miss bpPred bpIncorrect bpRate commitMisp

  simSeconds="$(get_stat "$stats" "simSeconds")"
  simInsts="$(get_stat "$stats" "simInsts")"
  numCycles="$(get_stat "$stats" "system.cpu.numCycles")"
  ipc="$(get_stat "$stats" "system.cpu.ipc")"
  cpi="$(get_stat "$stats" "system.cpu.cpi")"

  iMiss="$(get_stat_any "$stats" "system.cpu.icache.overallMissRate::total" "system.cpu.icache.demandMissRate::total")"
  dMiss="$(get_stat_any "$stats" "system.cpu.dcache.overallMissRate::total" "system.cpu.dcache.demandMissRate::total")"
  l2Miss="$(get_stat_any "$stats" "system.l2cache.overallMissRate::total" "system.l2cache.demandMissRate::total")"

  bpPred="$(get_stat "$stats" "system.cpu.branchPred.condPredicted")"
  bpIncorrect="$(get_stat "$stats" "system.cpu.branchPred.condIncorrect")"
  bpRate="$(calc_ratio "$bpIncorrect" "$bpPred")"
  commitMisp="$(get_stat "$stats" "system.cpu.commit.branchMispredicts")"

  echo "$arch,$question,$workload,$size_kb,$simSeconds,$simInsts,$numCycles,$ipc,$cpi,$iMiss,$dMiss,$l2Miss,$bpPred,$bpIncorrect,$bpRate,$commitMisp,$outdir" >> "$CSV"
}

run_arch_a7() {
  for size in 1 2 4 8 16; do
    run_one "a7" "Q4" "$CFG_A7" "$size" "dijkstra_large"
    run_one "a7" "Q4" "$CFG_A7" "$size" "blowfish_large"
  done
}

run_arch_a15() {
  for size in 2 4 8 16 32; do
    run_one "a15" "Q5" "$CFG_A15" "$size" "dijkstra_large"
    run_one "a15" "Q5" "$CFG_A15" "$size" "blowfish_large"
  done
}

if [ "$ARCH_MODE" = "a7" ]; then
  run_arch_a7
elif [ "$ARCH_MODE" = "a15" ]; then
  run_arch_a15
else
  run_arch_a7
  run_arch_a15
fi

chmod +x "$CMDS"

echo
echo "Done."
echo "Summary CSV: $CSV"
echo "Executed commands: $CMDS"
echo "Raw outputs: $OUT"
