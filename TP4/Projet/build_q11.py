#!/usr/bin/env python3
import argparse
import csv
import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Row:
    arch: str
    question: str
    workload: str
    l1_kb: int
    ipc: float


def read_q45(path: str) -> List[Row]:
    rows: List[Row] = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                rows.append(
                    Row(
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Q11 energy efficiency CSV (IPC / mW)")
    ap.add_argument(
        "--q45",
        default="TP4/Projet/q45_m5out/q45_summary.csv",
        help="Input q45_summary.csv (IPC)",
    )
    ap.add_argument(
        "--outdir",
        default="TP4/Projet/q11_eff",
        help="Output directory",
    )
    args = ap.parse_args()

    rows = read_q45(args.q45)
    if not rows:
        raise SystemExit(f"No rows found in {args.q45}")

    # From statement (28 nm):
    # A7: 0.10 mW/MHz, fmax=1.0 GHz -> 100 mW
    # A15: 0.20 mW/MHz, fmax=2.5 GHz -> 500 mW
    power_mw = {"a7": 100.0, "a15": 500.0}

    def keep(r: Row) -> bool:
        if r.arch == "a7":
            return r.question == "Q4" and r.l1_kb in {1, 2, 4, 8, 16}
        if r.arch == "a15":
            return r.question == "Q5" and r.l1_kb in {2, 4, 8, 16, 32}
        return False

    out_rows = []
    for r in rows:
        if not keep(r):
            continue
        p = power_mw.get(r.arch)
        if p is None:
            continue
        eff = r.ipc / p
        out_rows.append(
            {
                "arch": r.arch,
                "workload": r.workload,
                "l1_kB": str(r.l1_kb),
                "ipc": f"{r.ipc:.6f}",
                "power_mW": f"{p:.1f}",
                "eff_ipc_per_mW": f"{eff:.8f}",
            }
        )

    out_rows.sort(key=lambda x: (x["arch"], x["workload"], int(x["l1_kB"])))

    os.makedirs(args.outdir, exist_ok=True)
    out_csv = os.path.join(args.outdir, "q11_summary.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["arch", "workload", "l1_kB", "ipc", "power_mW", "eff_ipc_per_mW"],
        )
        w.writeheader()
        w.writerows(out_rows)

    print("Wrote:")
    print(" ", out_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
