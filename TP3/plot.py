# plot_from_results.py
# Parse results.txt (format: RUN  numCycles  CPI) and generate bar graphs.

import re
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

RESULTS_FILE = "results.txt"

# Expected RUN format: m5out_<dataset>_M<M>
RUN_RE = re.compile(r"^m5out_(min|med|max)_M(\d+)$")

def parse_results(path: str):
    data_cycles = defaultdict(dict)  # dataset -> M -> cycles
    data_cpi = defaultdict(dict)     # dataset -> M -> cpi
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("RUN"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue

            run, cycles_s, cpi_s = parts[0], parts[1], parts[2]
            m = RUN_RE.match(run)
            if not m:
                continue

            dataset = m.group(1)
            M = int(m.group(2))

            if cycles_s != "NA":
                data_cycles[dataset][M] = int(cycles_s)
            if cpi_s != "NA":
                data_cpi[dataset][M] = float(cpi_s)

    return data_cycles, data_cpi

def make_grouped_bar(x_labels, series_dict, ylabel, out_png):
    datasets = ["min", "med", "max"]
    x = np.arange(len(x_labels))
    width = 0.25

    fig, ax = plt.subplots()
    for i, d in enumerate(datasets):
        y = [series_dict.get(d, {}).get(M, np.nan) for M in x_labels]
        ax.bar(x + i * width, y, width, label=d)

    ax.set_xlabel("Nombre d'unités fonctionnelles (M)")
    ax.set_ylabel(ylabel)
    ax.set_xticks(x + width)
    ax.set_xticklabels([str(m) for m in x_labels])
    ax.legend(title="Dataset")

    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.show()

def main():
    cycles, cpi = parse_results(RESULTS_FILE)

    # collect Ms present across datasets
    Ms = sorted({M for d in cycles for M in cycles[d]} | {M for d in cpi for M in cpi[d]})
    if not Ms:
        raise RuntimeError(f"No data parsed from {RESULTS_FILE}. Check file format/paths.")

    make_grouped_bar(Ms, cycles, "Nombre de cycles", "cycles_bargraph.png")
    make_grouped_bar(Ms, cpi, "CPI", "cpi_bargraph.png")

if __name__ == "__main__":
    main()
