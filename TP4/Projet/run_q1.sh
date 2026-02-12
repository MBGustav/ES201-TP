#!/bin/bash
set -e

# Simple script for TP4 Q1
# Usage:
#   ./run_q1.sh
#   ./run_q1.sh a15
#   ./run_q1.sh both
#
# You can also pass the gem5 path as the second argument:
#   ./run_q1.sh both /path/to/gem5.opt

ARCH="${1:-a7}"
GEM5="${2:-/home/josedanielchg/Projects/architecture-microprocesseurs/gem5/build/RISCV/gem5.opt}"

if [ "$ARCH" != "a7" ] && [ "$ARCH" != "a15" ] && [ "$ARCH" != "both" ]; then
  echo "Error: use a7, a15 or both"
  exit 1
fi

if [ ! -x "$GEM5" ]; then
  echo "Error: gem5 not found at: $GEM5"
  exit 1
fi

BASE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$BASE/../.." && pwd)"

DIJ_DIR="$BASE/dijkstra"
BF_DIR="$BASE/blowfish"
OUT="$BASE/q1_m5out"
mkdir -p "$OUT"

echo "== Building benchmarks =="
make -C "$DIJ_DIR" clean all
make -C "$BF_DIR" clean all

extract_mix() {
  STATS_FILE="$1"
  OUT_FILE="$2"

  TMP_FILE="${OUT_FILE}.tmp"

  awk '
  BEGIN {
    source = 0
  }
  $1 ~ /^system\.cpu\./ {
    m = $1
    v = $2 + 0

    # Prefer commit.committedInstType_0 if present.
    # Use commitStats0.committedInstType only as fallback.
    if (m ~ /commit\.committedInstType_0::/) {
      source = 1
    } else if (source == 0 && m ~ /commitStats0\.committedInstType::/) {
      source = 2
    } else {
      next
    }

    if ((source == 1 && m ~ /commit\.committedInstType_0::/) ||
        (source == 2 && m ~ /commitStats0\.committedInstType::/)) {
      c = m
      sub(/^.*::/, "", c)
      if (c == "total" || c == "class") next
      cnt[c] += v
      total += v
    }
  }
  END {
    for (k in cnt) {
      p = (total > 0) ? (100.0 * cnt[k] / total) : 0
      printf "%s,%.0f,%.6f\n", k, cnt[k], p
    }
  }' "$STATS_FILE" | sort > "$TMP_FILE"

  echo "class,count,pct" > "$OUT_FILE"
  cat "$TMP_FILE" >> "$OUT_FILE"
  rm -f "$TMP_FILE"
}

run_arch() {
  A="$1"

  if [ "$A" = "a7" ]; then
    CFG="$ROOT/TP4/se_A7.py"
  else
    CFG="$ROOT/TP4/se_A15.py"
  fi

  DIJ_OUT="$OUT/m5out_q1_${A}_dijkstra"
  BF_OUT="$OUT/m5out_q1_${A}_blowfish"
  BF_ENC="$OUT/output_q1_${A}.enc"

  echo "== Running Dijkstra ($A) =="
  rm -rf "$DIJ_OUT"
  "$GEM5" -d "$DIJ_OUT" "$CFG" \
    --cmd "$DIJ_DIR/dijkstra_large.riscv" \
    --options "$DIJ_DIR/input.dat"

  echo "== Running Blowfish ($A) =="
  rm -rf "$BF_OUT"
  "$GEM5" -d "$BF_OUT" "$CFG" \
    --cmd "$BF_DIR/bf.riscv" \
    --options e "$BF_DIR/input_large.asc" "$BF_ENC" 0123456789ABCDEF

  DIJ_CSV="$OUT/q1_${A}_dijkstra.csv"
  BF_CSV="$OUT/q1_${A}_blowfish.csv"
  SUM_CSV="$OUT/q1_summary_${A}.csv"
  SUM_TMP="$SUM_CSV.tmp"

  extract_mix "$DIJ_OUT/stats.txt" "$DIJ_CSV"
  extract_mix "$BF_OUT/stats.txt" "$BF_CSV"

  # Final table for the Q1 report
  awk -F',' '
    FNR == 1 { next }
    NR == FNR {
      if ($1 == "class" || $1 == "total") next
      d[$1] = $3
      seen[$1] = 1
      next
    }
    {
      if ($1 == "class" || $1 == "total") next
      b[$1] = $3
      seen[$1] = 1
    }
    END {
      for (k in seen) {
        dp = (k in d) ? d[k] : 0
        bp = (k in b) ? b[k] : 0
        printf "%s,%.6f,%.6f\n", k, dp, bp
      }
    }' "$DIJ_CSV" "$BF_CSV" | sort > "$SUM_TMP"
  echo "class,dijkstra_pct,blowfish_pct" > "$SUM_CSV"
  cat "$SUM_TMP" >> "$SUM_CSV"
  rm -f "$SUM_TMP"

  echo "Done: $SUM_CSV"
}

if [ "$ARCH" = "both" ]; then
  run_arch a7
  run_arch a15
else
  run_arch "$ARCH"
fi

echo
echo "Finished."
echo "Results in: $OUT"
