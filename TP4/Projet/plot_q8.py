#!/usr/bin/env python3
import argparse
import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt


def read_rows(path):
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                rows.append(
                    {
                        "arch": r["arch"].strip(),
                        "l1_kB": int(r["l1_kB"]),
                        "l1_total_mm2": float(r["l1_total_mm2"]),
                        "l2_one_mm2": float(r["l2_one_mm2"]),
                        "core_wo_l1_mm2": float(r["core_wo_l1_mm2"]),
                        "total_core_l1_l2_mm2": float(r["total_core_l1_l2_mm2"]),
                    }
                )
            except Exception:
                continue
    return rows


def split_by_arch(rows):
    data = defaultdict(list)
    for r in rows:
        data[r["arch"]].append(r)
    for arch in data:
        data[arch] = sorted(data[arch], key=lambda x: x["l1_kB"])
    return data


def plot_l1_area(data, out_png):
    plt.figure(figsize=(8, 5))
    for arch, rows in sorted(data.items()):
        x = [r["l1_kB"] for r in rows]
        y = [r["l1_total_mm2"] for r in rows]
        plt.plot(x, y, marker="o", linewidth=1.8, label=arch.upper())

    plt.xlabel("L1 size (kB), with L1I = L1D")
    plt.ylabel("L1 total area (mm^2)")
    plt.title("Q8 - L1 total area vs L1 size")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=180)
    plt.close()


def plot_total_area(data, out_png):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.5), sharey=False)

    # Left: absolute total area vs L1 size
    ax = axs[0]
    for arch, rows in sorted(data.items()):
        x = [r["l1_kB"] for r in rows]
        y = [r["total_core_l1_l2_mm2"] for r in rows]
        ax.plot(x, y, marker="o", linewidth=1.8, label=arch.upper())
    ax.set_title("Total area vs L1 size")
    ax.set_xlabel("L1 size (kB)")
    ax.set_ylabel("Total area (mm^2)")
    ax.grid(alpha=0.3)
    ax.legend()

    # Right: delta wrt the smallest tested L1
    ax = axs[1]
    for arch, rows in sorted(data.items()):
        x = [r["l1_kB"] for r in rows]
        y = [r["total_core_l1_l2_mm2"] for r in rows]
        if not y:
            continue
        base = y[0]
        dy = [v - base for v in y]
        ax.plot(x, dy, marker="o", linewidth=1.8, label=arch.upper())
    ax.set_title("Extra total area vs smallest L1")
    ax.set_xlabel("L1 size (kB)")
    ax.set_ylabel("Delta area (mm^2)")
    ax.grid(alpha=0.3)
    ax.legend()

    fig.suptitle("Q8 - New total area (core + L1 + L2)")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(out_png, dpi=180)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Plot Q8 CACTI surface results")
    ap.add_argument("--csv", default="TP4/Projet/q8_cacti/q8_summary.csv")
    ap.add_argument("--outdir", default="TP4/Projet/q8_cacti/plots")
    args = ap.parse_args()

    rows = read_rows(args.csv)
    if not rows:
        raise SystemExit(f"No rows found in {args.csv}")

    data = split_by_arch(rows)

    os.makedirs(args.outdir, exist_ok=True)
    out1 = os.path.join(args.outdir, "q8_l1_area_vs_size.png")
    out2 = os.path.join(args.outdir, "q8_total_area_vs_size.png")

    plot_l1_area(data, out1)
    plot_total_area(data, out2)

    print("Wrote plots:")
    print(" ", out1)
    print(" ", out2)


if __name__ == "__main__":
    main()
