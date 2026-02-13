#!/usr/bin/env python3
import argparse
import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt


def read_rows(path):
    rows = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                rows.append(
                    {
                        "arch": row["arch"].strip(),
                        "workload": row["workload"].strip(),
                        "l1_kB": int(row["l1_kB"]),
                        "eff": float(row["eff_ipc_per_mm2"]),
                    }
                )
            except Exception:
                continue
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Plot Q9 surface efficiency (IPC/mm^2)")
    ap.add_argument("--csv", default="TP4/Projet/q9_eff/q9_summary.csv")
    ap.add_argument("--outdir", default="TP4/Projet/q9_eff/plots")
    args = ap.parse_args()

    rows = read_rows(args.csv)
    if not rows:
        raise SystemExit(f"No rows in {args.csv}")

    data = defaultdict(lambda: defaultdict(list))
    for r in rows:
        data[r["arch"]][r["workload"]].append(r)

    for arch in data:
        for wl in data[arch]:
            data[arch][wl] = sorted(data[arch][wl], key=lambda x: x["l1_kB"])

    os.makedirs(args.outdir, exist_ok=True)

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.5), sharey=False)

    def plot_arch(ax, arch, title):
        wl_items = sorted(data.get(arch, {}).items())
        if not wl_items:
            ax.text(0.5, 0.5, f"No data for {arch}", ha="center", va="center")
            ax.set_axis_off()
            return
        for wl, pts in wl_items:
            x = [p["l1_kB"] for p in pts]
            y = [p["eff"] for p in pts]
            label = wl.replace("_large", "")
            ax.plot(x, y, marker="o", linewidth=1.8, label=label)
        ax.set_title(title)
        ax.set_xlabel("L1 size (kB)")
        ax.set_ylabel("Surface efficiency (IPC / mm^2)")
        ax.set_xticks(sorted({p["l1_kB"] for wl, pts in wl_items for p in pts}))
        ax.grid(alpha=0.3)
        ax.legend()

    plot_arch(axs[0], "a7", "A7 (Q4 IPC) - surface efficiency")
    plot_arch(axs[1], "a15", "A15 (Q5 IPC) - surface efficiency")

    fig.suptitle("Q9 - Efficacite surfacique = IPC / surface(mm^2)")
    fig.tight_layout(rect=[0, 0, 1, 0.92])

    out_png = os.path.join(args.outdir, "plot_q9_efficiency.png")
    fig.savefig(out_png, dpi=180)
    plt.close(fig)

    print("Wrote:")
    print(" ", out_png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
