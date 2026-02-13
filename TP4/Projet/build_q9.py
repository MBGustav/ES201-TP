#!/usr/bin/env python3
import argparse
import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Q45Row:
    arch: str
    question: str
    workload: str
    l1_kb: int
    ipc: float


@dataclass(frozen=True)
class Q8Row:
    arch: str
    l1_kb: int
    total_area_mm2: float


def read_q45(path: str) -> List[Q45Row]:
    rows: List[Q45Row] = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                rows.append(
                    Q45Row(
                        arch=row.get("arch", "").strip(),
                        question=row.get("question", "").strip(),
                        workload=row.get("workload", "").strip(),
                        l1_kb=int(row.get("l1_kB", "0")),
                        ipc=float(row.get("ipc", "nan")),
                    )
                )
            except Exception:
                continue
    return rows


def read_q8(path: str) -> Dict[Tuple[str, int], Q8Row]:
    out: Dict[Tuple[str, int], Q8Row] = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                arch = row.get("arch", "").strip()
                l1_kb = int(row.get("l1_kB", "0"))
                total_area = float(row.get("total_core_l1_l2_mm2", "nan"))
                out[(arch, l1_kb)] = Q8Row(arch=arch, l1_kb=l1_kb, total_area_mm2=total_area)
            except Exception:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Q9 surface efficiency CSV (IPC / mm^2)")
    ap.add_argument(
        "--q45",
        default="TP4/Projet/q45_m5out/q45_summary.csv",
        help="Input q45_summary.csv (IPC)",
    )
    ap.add_argument(
        "--q8",
        default="TP4/Projet/q8_cacti/q8_summary.csv",
        help="Input q8_summary.csv (area)",
    )
    ap.add_argument(
        "--outdir",
        default="TP4/Projet/q9_eff",
        help="Output directory",
    )
    args = ap.parse_args()

    q45_rows = read_q45(args.q45)
    if not q45_rows:
        raise SystemExit(f"No rows found in {args.q45}")

    q8_map = read_q8(args.q8)
    if not q8_map:
        raise SystemExit(f"No rows found in {args.q8}")

    os.makedirs(args.outdir, exist_ok=True)
    out_csv = os.path.join(args.outdir, "q9_summary.csv")

    def keep(row: Q45Row) -> bool:
        if row.arch == "a7":
            return row.question == "Q4" and row.l1_kb in {1, 2, 4, 8, 16}
        if row.arch == "a15":
            return row.question == "Q5" and row.l1_kb in {2, 4, 8, 16, 32}
        return False

    out_rows = []
    for r in q45_rows:
        if not keep(r):
            continue
        area = q8_map.get((r.arch, r.l1_kb))
        if area is None:
            continue
        eff = r.ipc / area.total_area_mm2 if area.total_area_mm2 else float("nan")
        out_rows.append(
            {
                "arch": r.arch,
                "workload": r.workload,
                "l1_kB": str(r.l1_kb),
                "ipc": f"{r.ipc:.6f}",
                "surface_mm2": f"{area.total_area_mm2:.7f}",
                "eff_ipc_per_mm2": f"{eff:.7f}",
            }
        )

    out_rows.sort(key=lambda x: (x["arch"], x["workload"], int(x["l1_kB"])))

    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["arch", "workload", "l1_kB", "ipc", "surface_mm2", "eff_ipc_per_mm2"],
        )
        w.writeheader()
        w.writerows(out_rows)

    print("Wrote:")
    print(" ", out_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
