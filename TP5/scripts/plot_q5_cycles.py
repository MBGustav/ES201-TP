#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_L2 = os.path.join(SCRIPT_DIR, "summary_L2_upto8.csv")
CSV_NOL2 = os.path.join(SCRIPT_DIR, "summary_noL2_upto16.csv")

OUTDIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "doc", "figures"))

def load_csv(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No existe el archivo: {path}")

    df = pd.read_csv(path)
    if "threads" not in df.columns or "cycles_app" not in df.columns:
        raise ValueError(f"CSV inválido ({path}). Columnas esperadas: threads, cycles_app")

    df["threads"] = pd.to_numeric(df["threads"], errors="raise").astype(int)
    df["cycles_app"] = pd.to_numeric(df["cycles_app"], errors="raise").astype(int)
    return df.sort_values("threads").reset_index(drop=True)

def plot_one(df: pd.DataFrame, title: str, outpath: str):
    x = df["threads"].tolist()
    y = df["cycles_app"].tolist()

    plt.figure()
    plt.plot(x, y, marker="o")
    plt.xlabel("Threads (nthreads = ncores)")
    plt.ylabel("Cycles d'exécution (cycles_app)")
    plt.title(title)
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.xticks(x)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()

def main():
    os.makedirs(OUTDIR, exist_ok=True)

    df_l2 = load_csv(CSV_L2)
    df_nol2 = load_csv(CSV_NOL2)

    out_l2 = os.path.join(OUTDIR, "Q5_cycles_A7_L2_upto8.png")
    out_nol2 = os.path.join(OUTDIR, "Q5_cycles_A7_noL2_upto16.png")

    plot_one(df_l2, "Q5 — Cycles vs Threads (A7, avec L2, T≤8)", out_l2)
    plot_one(df_nol2, "Q5 — Cycles vs Threads (A7, sans L2, T≤16)", out_nol2)

    print("OK. Figures générées :")
    print(" -", out_l2)
    print(" -", out_nol2)

if __name__ == "__main__":
    main()