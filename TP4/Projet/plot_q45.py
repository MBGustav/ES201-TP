#!/usr/bin/env python3
import argparse
import csv
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


@dataclass(frozen=True)
class Row:
    arch: str
    question: str
    workload: str
    l1_kb: int
    sim_seconds: Optional[float]
    sim_insts: Optional[int]
    num_cycles: Optional[int]
    ipc: Optional[float]
    cpi: Optional[float]
    icache_miss: Optional[float]
    dcache_miss: Optional[float]
    l2_miss: Optional[float]
    bp_mispred_rate: Optional[float]
    branch_mispredicts: Optional[int]
    outdir: str


def _to_int(value: str) -> Optional[int]:
    value = value.strip()
    if not value or value == "NA":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _to_float(value: str) -> Optional[float]:
    value = value.strip()
    if not value or value == "NA":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def read_rows(csv_path: str) -> List[Row]:
    rows: List[Row] = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                Row(
                    arch=r.get("arch", "").strip(),
                    question=r.get("question", "").strip(),
                    workload=r.get("workload", "").strip(),
                    l1_kb=int(r.get("l1_kB", "0")),
                    sim_seconds=_to_float(r.get("simSeconds", "NA")),
                    sim_insts=_to_int(r.get("simInsts", "NA")),
                    num_cycles=_to_int(r.get("numCycles", "NA")),
                    ipc=_to_float(r.get("ipc", "NA")),
                    cpi=_to_float(r.get("cpi", "NA")),
                    icache_miss=_to_float(r.get("icache_miss", "NA")),
                    dcache_miss=_to_float(r.get("dcache_miss", "NA")),
                    l2_miss=_to_float(r.get("l2_miss", "NA")),
                    bp_mispred_rate=_to_float(r.get("bp_condMispredRate", "NA")),
                    branch_mispredicts=_to_int(r.get("commit_branchMispredicts", "NA")),
                    outdir=r.get("outdir", "").strip(),
                )
            )
    return rows


def group_rows(rows: List[Row]) -> Dict[Tuple[str, str, str], List[Row]]:
    groups: Dict[Tuple[str, str, str], List[Row]] = {}
    for r in rows:
        key = (r.arch, r.question, r.workload)
        groups.setdefault(key, []).append(r)
    for key in list(groups.keys()):
        groups[key] = sorted(groups[key], key=lambda x: x.l1_kb)
    return groups


def choose_best_l1(rows: List[Row]) -> Optional[int]:
    # Prefer minimum cycles if present; else maximum IPC.
    with_cycles = [r for r in rows if r.num_cycles is not None]
    if with_cycles:
        best = min(with_cycles, key=lambda r: r.num_cycles)  # type: ignore[arg-type]
        return best.l1_kb
    with_ipc = [r for r in rows if r.ipc is not None]
    if with_ipc:
        best = max(with_ipc, key=lambda r: r.ipc)  # type: ignore[arg-type]
        return best.l1_kb
    return None


def _plot_line(ax, x: List[int], y: List[Optional[float]], label: str, color: str):
    xs: List[int] = []
    ys: List[float] = []
    for xi, yi in zip(x, y):
        if yi is None or (isinstance(yi, float) and (math.isnan(yi) or math.isinf(yi))):
            continue
        xs.append(xi)
        ys.append(float(yi))
    if not xs:
        ax.text(0.5, 0.5, "NA", transform=ax.transAxes, ha="center", va="center")
        return
    ax.plot(xs, ys, marker="o", linewidth=1.5, label=label, color=color)


def plot_group(outdir: str, key: Tuple[str, str, str], rows: List[Row]) -> str:
    arch, question, workload = key
    sizes = [r.l1_kb for r in rows]

    best = choose_best_l1(rows)
    title = f"{arch.upper()} {question} - {workload}"
    if best is not None:
        title += f" (best L1 = {best}kB)"

    fig, axs = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    fig.suptitle(title, fontsize=12)

    # IPC
    ax = axs[0, 0]
    _plot_line(ax, sizes, [r.ipc for r in rows], "IPC", "#1f77b4")
    ax.set_xlabel("L1 size (kB)  (L1I=L1D)")
    ax.set_ylabel("IPC")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(sizes)
    if best is not None:
        ax.axvline(best, color="red", linestyle="--", alpha=0.5)

    # Cycles
    ax = axs[0, 1]
    cycles_m = [None if r.num_cycles is None else (r.num_cycles / 1e6) for r in rows]
    _plot_line(ax, sizes, cycles_m, "Cycles (M)", "#ff7f0e")
    ax.set_xlabel("L1 size (kB)  (L1I=L1D)")
    ax.set_ylabel("CPU cycles (millions)")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(sizes)
    if best is not None:
        ax.axvline(best, color="red", linestyle="--", alpha=0.5)

    # Cache miss rates
    ax = axs[1, 0]
    _plot_line(ax, sizes, [r.icache_miss for r in rows], "L1I miss rate", "#2ca02c")
    _plot_line(ax, sizes, [r.dcache_miss for r in rows], "L1D miss rate", "#d62728")
    _plot_line(ax, sizes, [r.l2_miss for r in rows], "L2 miss rate", "#9467bd")
    ax.set_xlabel("L1 size (kB)  (L1I=L1D)")
    ax.set_ylabel("Miss rate")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(sizes)
    ax.legend(fontsize=9)

    # Branch predictor mispred rate
    ax = axs[1, 1]
    _plot_line(ax, sizes, [r.bp_mispred_rate for r in rows], "Cond mispred rate", "#8c564b")
    ax.set_xlabel("L1 size (kB)  (L1I=L1D)")
    ax.set_ylabel("Mispred rate")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(sizes)

    out_path = os.path.join(outdir, f"plot_{question.lower()}_{arch}_{workload}.png")
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Plot Q4/Q5 results from q45_summary.csv")
    ap.add_argument(
        "--csv",
        default="TP4/Projet/q45_m5out/q45_summary.csv",
        help="Path to q45_summary.csv",
    )
    ap.add_argument(
        "--outdir",
        default="TP4/Projet/q45_m5out/plots",
        help="Output directory for PNG plots",
    )
    args = ap.parse_args()

    rows = read_rows(args.csv)
    if not rows:
        raise SystemExit(f"No rows found in {args.csv}")

    os.makedirs(args.outdir, exist_ok=True)

    groups = group_rows(rows)
    outputs: List[str] = []
    for key, g in sorted(groups.items()):
        outputs.append(plot_group(args.outdir, key, g))

    print("Wrote plots:")
    for p in outputs:
        print("  ", p)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

