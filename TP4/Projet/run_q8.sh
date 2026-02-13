#!/bin/bash
set -e

# Q8 surface sweep (CACTI)
# Usage:
#   ./run_q8.sh
#   ./run_q8.sh a7
#   ./run_q8.sh a15
#   ./run_q8.sh both TP4/Projet/cacti65

ARCH_MODE="${1:-both}"   # a7 | a15 | both
CACTI_DIR="${2:-TP4/Projet/cacti65}"

if [ "$ARCH_MODE" != "a7" ] && [ "$ARCH_MODE" != "a15" ] && [ "$ARCH_MODE" != "both" ]; then
  echo "Error: first arg must be a7, a15 or both"
  exit 1
fi

CACTI_BIN="$CACTI_DIR/cacti"
BASE_CFG="$CACTI_DIR/cache.cfg"
OUT_DIR="TP4/Projet/q8_cacti"
CSV="$OUT_DIR/q8_summary.csv"
CMDS="$OUT_DIR/q8_commands.sh"

if [ ! -x "$CACTI_BIN" ]; then
  echo "Error: cacti not found/executable at $CACTI_BIN"
  echo "Build it first: cd $CACTI_DIR && make clean && make"
  exit 1
fi

if [ ! -f "$BASE_CFG" ]; then
  echo "Error: base config not found: $BASE_CFG"
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "#!/bin/bash" > "$CMDS"
echo "set -e" >> "$CMDS"

echo "arch,l1_kB,l1_block,l1_assoc,l1_data_mm2,l1_tag_mm2,l1_one_mm2,l1_total_mm2,l2_data_mm2,l2_tag_mm2,l2_one_mm2,core_wo_l1_mm2,total_core_l1_l2_mm2,cfg_l1,cfg_l2,out_l1,out_l2" > "$CSV"

A7_CORE="0.3731364"
A15_CORE="1.9308701"
Q7_CSV="$CACTI_DIR/q7_area_summary.csv"
if [ -f "$Q7_CSV" ]; then
  A7_FROM_Q7="$(awk -F, '$1=="A7"{print $7}' "$Q7_CSV")"
  A15_FROM_Q7="$(awk -F, '$1=="A15"{print $7}' "$Q7_CSV")"
  if [ -n "$A7_FROM_Q7" ]; then A7_CORE="$A7_FROM_Q7"; fi
  if [ -n "$A15_FROM_Q7" ]; then A15_CORE="$A15_FROM_Q7"; fi
fi

make_cfg() {
  local out_cfg="$1"
  local size_bytes="$2"
  local block_bytes="$3"
  local assoc="$4"
  local tech_um="$5"

  cp "$BASE_CFG" "$out_cfg"
  sed -i "s|^-size (bytes) .*|-size (bytes) ${size_bytes}|" "$out_cfg"
  sed -i "s|^-block size (bytes) .*|-block size (bytes) ${block_bytes}|" "$out_cfg"
  sed -i "s|^-associativity .*|-associativity ${assoc}|" "$out_cfg"
  sed -i "s|^-technology (u) .*|-technology (u) ${tech_um}|" "$out_cfg"
  sed -i 's|^-cache type ".*"|-cache type "cache"|' "$out_cfg"
}

run_cacti() {
  local cfg="$1"
  local out_txt="$2"
  printf "%q %q %q > %q\n" "$CACTI_BIN" "-infile" "$cfg" "$out_txt" >> "$CMDS"
  "$CACTI_BIN" -infile "$cfg" > "$out_txt"
}

get_area_data() {
  awk '/Data array: Area \(mm2\):/ {print $5; exit}' "$1"
}

get_area_tag() {
  awk '/Tag array: Area \(mm2\):/ {print $5; exit}' "$1"
}

sum2() {
  awk -v a="$1" -v b="$2" 'BEGIN{ if(a==""||b==""||a=="NA"||b=="NA") print "NA"; else printf "%.7f", (a+0)+(b+0) }'
}

mul2() {
  awk -v a="$1" -v k="$2" 'BEGIN{ if(a==""||a=="NA") print "NA"; else printf "%.7f", (a+0)*(k+0) }'
}

sum3() {
  awk -v a="$1" -v b="$2" -v c="$3" 'BEGIN{ if(a==""||b==""||c==""||a=="NA"||b=="NA"||c=="NA") print "NA"; else printf "%.7f", (a+0)+(b+0)+(c+0) }'
}

sweep_arch() {
  local arch="$1"
  local core_wo_l1="$2"
  local l1_block="$3"
  local l1_assoc="$4"
  local l2_block="$5"
  local l2_assoc="$6"
  shift 6
  local sizes=("$@")

  local l2_cfg="$OUT_DIR/cache_${arch}_L2_512kB_32nm.cfg"
  local l2_out="$OUT_DIR/result_${arch}_L2_512kB_32nm.txt"

  make_cfg "$l2_cfg" 524288 "$l2_block" "$l2_assoc" 0.032
  run_cacti "$l2_cfg" "$l2_out"

  local l2_data l2_tag l2_one
  l2_data="$(get_area_data "$l2_out")"
  l2_tag="$(get_area_tag "$l2_out")"
  l2_one="$(sum2 "$l2_data" "$l2_tag")"

  for kb in "${sizes[@]}"; do
    local bytes=$((kb * 1024))
    local l1_cfg="$OUT_DIR/cache_${arch}_L1_${kb}kB_32nm.cfg"
    local l1_out="$OUT_DIR/result_${arch}_L1_${kb}kB_32nm.txt"

    make_cfg "$l1_cfg" "$bytes" "$l1_block" "$l1_assoc" 0.032
    run_cacti "$l1_cfg" "$l1_out"

    local l1_data l1_tag l1_one l1_total total_new
    l1_data="$(get_area_data "$l1_out")"
    l1_tag="$(get_area_tag "$l1_out")"
    l1_one="$(sum2 "$l1_data" "$l1_tag")"
    l1_total="$(mul2 "$l1_one" 2)"
    total_new="$(sum3 "$core_wo_l1" "$l1_total" "$l2_one")"

    echo "$arch,$kb,$l1_block,$l1_assoc,$l1_data,$l1_tag,$l1_one,$l1_total,$l2_data,$l2_tag,$l2_one,$core_wo_l1,$total_new,$l1_cfg,$l2_cfg,$l1_out,$l2_out" >> "$CSV"

    echo "[$arch] L1=${kb}kB -> L1_total=${l1_total} mm2 | total(core+L1+L2)=${total_new} mm2"
  done
}

if [ "$ARCH_MODE" = "a7" ] || [ "$ARCH_MODE" = "both" ]; then
  # A7: L1 32B/2-way, L2 512KB 32B/8-way
  sweep_arch "a7" "$A7_CORE" 32 2 32 8 1 2 4 8 16
fi

if [ "$ARCH_MODE" = "a15" ] || [ "$ARCH_MODE" = "both" ]; then
  # A15: L1 64B/2-way, L2 512KB 64B/16-way
  sweep_arch "a15" "$A15_CORE" 64 2 64 16 2 4 8 16 32
fi

chmod +x "$CMDS"

echo
echo "Done."
echo "CSV: $CSV"
echo "Commands: $CMDS"
echo "Outputs: $OUT_DIR"
