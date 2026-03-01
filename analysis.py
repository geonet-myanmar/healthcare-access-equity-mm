"""
Myanmar Hospital Access Equity Analysis
========================================
Measures inequality in hospital accessibility across Myanmar's states and
regions using Gini coefficients derived from population-weighted Lorenz curves.

Data source:
    OpenStreetMap / HOT Raw Data API
    https://github.com/hotosm/raw-data-api
    Exported: 2026-02-12  |  License: ODbL 1.0

Usage:
    python analysis.py
    python analysis.py --threshold 3600
    python analysis.py --threshold 1800 --plot

Arguments:
    --threshold   Travel-time threshold in seconds (default: 3600 = 60 min).
                  Must be one of: 600 1200 1800 2400 3000 3600 4200 4800
                                  5400 6000 6600 7200
    --plot        Generate Lorenz curve and bar-chart visualisations
                  (requires matplotlib).
    --out         Directory to save outputs (default: ./output).
"""

import csv
import sys
import math
import argparse
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_FILE = Path(__file__).parent / "MMR_hospitals_access_wide.csv"

VALID_THRESHOLDS = [600, 1200, 1800, 2400, 3000, 3600, 4200, 4800,
                    5400, 6000, 6600, 7200]

# ADM2 district → parent ADM1 state/region mapping
# Source: Myanmar administrative divisions (14 states & regions)
DISTRICT_TO_STATE: dict[str, str] = {
    # Ayeyarwady Region (Irrawaddy Delta)
    "Pathein":       "Ayeyarwady",
    "Hinthada":      "Ayeyarwady",
    "Myaungmya":     "Ayeyarwady",
    "Maubin":        "Ayeyarwady",
    "Pyapon":        "Ayeyarwady",
    "Labutta":       "Ayeyarwady",
    # Bago Region
    "Bago":          "Bago",
    "Taungoo":       "Bago",
    "Pyay":          "Bago",
    "Thayarwady":    "Bago",
    # Chin State
    "Hakha":         "Chin",
    "Falam":         "Chin",
    "Mindat":        "Chin",
    # Kachin State
    "Myitkyina":     "Kachin",
    "Bhamo":         "Kachin",
    "Mohnyin":       "Kachin",
    "Puta-O":        "Kachin",
    # Kayah State
    "Loikaw":        "Kayah",
    "Bawlake":       "Kayah",
    # Kayin State
    "Hpa-An":        "Kayin",
    "Hpapun":        "Kayin",
    "Myawaddy":      "Kayin",
    "Kawkareik":     "Kayin",
    # Mon State
    "Mawlamyine":    "Mon",
    "Thaton":        "Mon",
    # Magway Region
    "Magway":        "Magway",
    "Minbu":         "Magway",
    "Thayet":        "Magway",
    "Pakokku":       "Magway",
    "Gangaw":        "Magway",
    # Mandalay Region
    "Mandalay":      "Mandalay",
    "Meiktila":      "Mandalay",
    "Pyinoolwin":    "Mandalay",
    "Kyaukse":       "Mandalay",
    "Nyaung-U":      "Mandalay",
    "Myingyan":      "Mandalay",
    "Yamethin":      "Mandalay",
    # Rakhine State
    "Sittwe":        "Rakhine",
    "Mrauk-U":       "Rakhine",
    "Kyaukpyu":      "Rakhine",
    "Thandwe":       "Rakhine",
    "Maungdaw":      "Rakhine",
    # Sagaing Region  (dataset uses "Saigang")
    "Sagaing":       "Saigang",
    "Monywa":        "Saigang",
    "Shwebo":        "Saigang",
    "Kanbalu":       "Saigang",
    "Kale":          "Saigang",
    "Tamu":          "Saigang",
    "Hkamti":        "Saigang",
    "Mawlaik":       "Saigang",
    "Yinmarbin":     "Saigang",
    "Katha":         "Saigang",
    "Oke Ta Ra":     "Saigang",
    # Shan State
    "Taunggyi":      "Shan",
    "Kengtung":      "Shan",
    "Langkho":       "Shan",
    "Lashio":        "Shan",
    "Kyaukme":       "Shan",
    "Loilen":        "Shan",
    "Monghsat":      "Shan",
    "Mongmit":       "Shan",
    "Muse":          "Shan",
    "Hopang":        "Shan",
    "Laukkaing":     "Shan",
    "Tachileik":     "Shan",
    "Matman":        "Shan",
    "Det Khi Na":    "Shan",
    # Tanintharyi Region  (dataset uses "Tanitharyi")
    "Dawei":         "Tanitharyi",
    "Myeik":         "Tanitharyi",
    "Kawthoung":     "Tanitharyi",
    # Yangon Region
    "Yangon (East)": "Yangon",
    "Yangon (North)":"Yangon",
    "Yangon (South)":"Yangon",
    "Yangon (West)": "Yangon",
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_rows(filepath: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """Return (adm0_rows, adm1_rows, adm2_rows) from the wide CSV."""
    with open(filepath, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    adm0 = [r for r in rows if r["admin_level"] == "ADM0"]
    adm1 = [r for r in rows if r["admin_level"] == "ADM1"]
    adm2 = [r for r in rows if r["admin_level"] == "ADM2"]
    return adm0, adm1, adm2


def get_record(rows: list[dict], name: str, threshold: int) -> dict | None:
    """Return the single row matching name and threshold, or None."""
    return next(
        (r for r in rows if r["name"] == name and int(r["range"]) == threshold),
        None,
    )

# ---------------------------------------------------------------------------
# Gini coefficient (population-weighted Lorenz curve)
# ---------------------------------------------------------------------------

def lorenz_gini(populations: list[float], access_rates: list[float]) -> float:
    """
    Compute the population-weighted Gini coefficient for hospital accessibility.

    Parameters
    ----------
    populations  : population of each administrative unit
    access_rates : percentage of that population within the travel-time
                   threshold of a hospital (0–100)

    Returns
    -------
    Gini coefficient in [0, 1].  Returns NaN when fewer than 2 units are
    supplied or when total accessible population is zero.

    Method
    ------
    1. Sort units by ascending access_rate (poorest access first).
    2. Build the Lorenz curve:
         x_k = cumulative share of total population
         y_k = cumulative share of "accessible" population
    3. Gini = 1 - 2 * (trapezoidal area under the Lorenz curve)

    A Gini of 0 means every unit has identical access rates (perfect equality).
    A Gini of 1 means one unit has all accessible population (perfect inequality).
    """
    if len(populations) < 2:
        return float("nan")

    # Sort ascending by access rate (Lorenz curve starts with least-served)
    paired = sorted(zip(access_rates, populations))
    rates = [p[0] for p in paired]
    pops  = [p[1] for p in paired]

    total_pop        = sum(pops)
    accessible       = [p * r / 100.0 for p, r in zip(pops, rates)]
    total_accessible = sum(accessible)

    if total_accessible == 0 or total_pop == 0:
        return float("nan")

    # Build Lorenz curve points (including origin)
    xs = [0.0]
    ys = [0.0]
    cum_pop = 0.0
    cum_acc = 0.0
    for pop, acc in zip(pops, accessible):
        cum_pop += pop / total_pop
        cum_acc += acc / total_accessible
        xs.append(cum_pop)
        ys.append(cum_acc)

    # Trapezoidal integration
    area = sum(
        (xs[i + 1] - xs[i]) * (ys[i] + ys[i + 1]) / 2.0
        for i in range(len(xs) - 1)
    )
    return 1.0 - 2.0 * area

# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------

def intra_regional_gini(
    adm2_rows: list[dict], threshold: int
) -> dict[str, dict]:
    """
    Compute the Gini coefficient for each ADM1 state/region using its
    constituent ADM2 districts.

    Returns a dict keyed by state name with sub-keys:
        gini, n_districts, districts (list of {name, pop, rate})
    """
    all_states = sorted(set(DISTRICT_TO_STATE.values()))
    results = {}

    for state in all_states:
        districts_in_state = [d for d, s in DISTRICT_TO_STATE.items() if s == state]
        pops, rates, district_records = [], [], []

        for district in districts_in_state:
            row = get_record(adm2_rows, district, threshold)
            if row:
                pop  = float(row["population"])
                rate = float(row["population_share"])
                pops.append(pop)
                rates.append(rate)
                district_records.append(
                    {"name": district, "population": pop, "access_rate": rate}
                )

        results[state] = {
            "gini":        lorenz_gini(pops, rates),
            "n_districts": len(pops),
            "districts":   sorted(district_records, key=lambda x: x["access_rate"]),
        }

    return results


def inter_regional_gini(adm1_rows: list[dict], threshold: int) -> dict:
    """
    Compute the national Gini across all 14 ADM1 states/regions.

    Returns a dict with keys:
        gini, regions (list of {name, population, access_rate})
    """
    pops, rates, region_records = [], [], []

    for row in adm1_rows:
        if int(row["range"]) == threshold:
            pop  = float(row["population"])
            rate = float(row["population_share"])
            pops.append(pop)
            rates.append(rate)
            region_records.append(
                {"name": row["name"], "population": pop, "access_rate": rate}
            )

    return {
        "gini":    lorenz_gini(pops, rates),
        "regions": sorted(region_records, key=lambda x: x["access_rate"]),
    }


def multi_threshold_gini(
    adm1_rows: list[dict], adm2_rows: list[dict]
) -> dict[str, dict[int, float]]:
    """
    Compute intra-regional Gini for every state and the national Gini at
    every available threshold.

    Returns nested dict:  matrix[state_or_"National"][threshold] = gini
    """
    all_states = sorted(set(DISTRICT_TO_STATE.values()))
    matrix: dict[str, dict[int, float]] = {s: {} for s in all_states}
    matrix["National"] = {}

    for t in VALID_THRESHOLDS:
        # National
        r = inter_regional_gini(adm1_rows, t)
        matrix["National"][t] = r["gini"]

        # Per-state
        per_state = intra_regional_gini(adm2_rows, t)
        for state, data in per_state.items():
            matrix[state][t] = data["gini"]

    return matrix

# ---------------------------------------------------------------------------
# Reporting / pretty-printing
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def report_intra(intra: dict[str, dict], threshold: int) -> None:
    minutes = threshold // 60
    print_section(
        f"INTRA-REGIONAL GINI  (threshold = {minutes} min)\n"
        f"  Inequality of hospital access across districts within each state/region"
    )
    print(f"  {'State/Region':<16} {'Gini':>7}  {'Districts':>10}  {'Mean access':>12}")
    print(f"  {'-'*16} {'-'*7}  {'-'*10}  {'-'*12}")

    for state, data in sorted(intra.items(), key=lambda x: -x[1]["gini"]):
        g  = data["gini"]
        n  = data["n_districts"]
        ds = data["districts"]
        if n == 0:
            continue
        mean_acc = sum(d["access_rate"] * d["population"] for d in ds) / sum(
            d["population"] for d in ds
        )
        flag = "  << YANGON" if state == "Yangon" else ""
        gini_str = f"{g:.4f}" if not math.isnan(g) else "  N/A "
        print(f"  {state:<16} {gini_str:>7}  {n:>10}  {mean_acc:>11.2f}%{flag}")


def report_inter(inter: dict, threshold: int) -> None:
    minutes = threshold // 60
    print_section(
        f"INTER-REGIONAL (NATIONAL) GINI  (threshold = {minutes} min)\n"
        f"  Inequality across all 14 states/regions\n"
        f"  National Gini = {inter['gini']:.4f}"
    )
    print(f"\n  {'State/Region':<16} {'Access rate':>12}  {'Population':>12}")
    print(f"  {'-'*16} {'-'*12}  {'-'*12}")
    for rec in inter["regions"]:
        flag = "  << YANGON" if rec["name"] == "Yangon" else ""
        print(
            f"  {rec['name']:<16} {rec['access_rate']:>11.2f}%"
            f"  {rec['population']/1e6:>10.2f}M{flag}"
        )


def report_yangon_districts(intra: dict[str, dict]) -> None:
    print_section("YANGON REGION — DISTRICT BREAKDOWN  (at chosen threshold)")
    districts = intra["Yangon"]["districts"]
    print(f"  {'District':<24} {'Access rate':>12}  {'Population':>12}")
    print(f"  {'-'*24} {'-'*12}  {'-'*12}")
    for d in districts:
        print(
            f"  {d['name']:<24} {d['access_rate']:>11.2f}%"
            f"  {d['population']/1e6:>10.3f}M"
        )
    g = intra["Yangon"]["gini"]
    print(f"\n  Yangon Gini = {g:.4f}")


def report_matrix(matrix: dict[str, dict[int, float]]) -> None:
    print_section("GINI BY THRESHOLD — FULL MATRIX  (intra-regional + national)")
    mins = [t // 60 for t in VALID_THRESHOLDS]
    header = f"  {'State/Region':<16}" + "".join(f"  {m:>4}m" for m in mins)
    print(header)
    print("  " + "-" * (16 + 7 * len(VALID_THRESHOLDS)))

    # Sort rows by 60-min Gini descending
    def sort_key(item):
        return -(item[1].get(3600, 0) or 0)

    for state, row in sorted(matrix.items(), key=sort_key):
        if state == "National":
            continue
        vals = "".join(
            f"  {row.get(t, float('nan')):.3f}" for t in VALID_THRESHOLDS
        )
        flag = "  << Yangon" if state == "Yangon" else ""
        print(f"  {state:<16}{vals}{flag}")

    # National row last
    nat = matrix["National"]
    vals = "".join(f"  {nat.get(t, float('nan')):.3f}" for t in VALID_THRESHOLDS)
    print(f"\n  {'National':<16}{vals}")

# ---------------------------------------------------------------------------
# Optional visualisation
# ---------------------------------------------------------------------------

def build_lorenz_data(
    populations: list[float], access_rates: list[float]
) -> tuple[list[float], list[float]]:
    """Return (xs, ys) Lorenz curve points (sorted ascending by rate)."""
    paired = sorted(zip(access_rates, populations))
    rates  = [p[0] for p in paired]
    pops   = [p[1] for p in paired]
    total_pop        = sum(pops)
    accessible       = [p * r / 100 for p, r in zip(pops, rates)]
    total_accessible = sum(accessible) or 1
    xs, ys = [0.0], [0.0]
    cp, ca = 0.0, 0.0
    for p, a in zip(pops, accessible):
        cp += p / total_pop
        ca += a / total_accessible
        xs.append(cp); ys.append(ca)
    return xs, ys


def plot_results(
    adm1_rows: list[dict], adm2_rows: list[dict],
    intra: dict, inter: dict, threshold: int, out_dir: Path
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("\n[WARNING] matplotlib not installed — skipping plots.")
        print("          Install with:  pip install matplotlib")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    minutes = threshold // 60

    # ── Plot 1: National Lorenz curve ────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 6))
    pops  = [r["population"]   for r in inter["regions"]]
    rates = [r["access_rate"]  for r in inter["regions"]]
    xs, ys = build_lorenz_data(pops, rates)
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Perfect equality")
    ax.fill_between(xs, xs, ys, alpha=0.15, color="steelblue")
    ax.plot(xs, ys, "o-", color="steelblue", linewidth=2,
            label=f"Lorenz curve (Gini = {inter['gini']:.4f})")
    # Annotate each region
    for i, rec in enumerate(sorted(inter["regions"], key=lambda r: r["access_rate"])):
        ax.annotate(rec["name"], (xs[i + 1], ys[i + 1]),
                    fontsize=7, ha="left",
                    color="darkred" if rec["name"] == "Yangon" else "black")
    ax.set_xlabel("Cumulative share of population", fontsize=11)
    ax.set_ylabel("Cumulative share of population with hospital access", fontsize=11)
    ax.set_title(
        f"National Lorenz Curve — Hospital Access @ {minutes}-min threshold\n"
        f"Myanmar (14 States/Regions)", fontsize=12
    )
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    path1 = out_dir / f"lorenz_national_{minutes}min.png"
    fig.tight_layout()
    fig.savefig(path1, dpi=150)
    plt.close(fig)
    print(f"  Saved: {path1}")

    # ── Plot 2: Intra-regional Gini bar chart ────────────────────────────────
    states_sorted = sorted(
        [(s, d["gini"]) for s, d in intra.items() if not math.isnan(d["gini"])],
        key=lambda x: x[1]
    )
    labels = [s[0] for s in states_sorted]
    ginis  = [s[1] for s in states_sorted]
    colors = ["tomato" if l == "Yangon" else "steelblue" for l in labels]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(labels, ginis, color=colors, edgecolor="white", height=0.7)
    ax.axvline(inter["gini"], color="black", linewidth=1.5, linestyle="--",
               label=f"National Gini = {inter['gini']:.4f}")
    for bar, g in zip(bars, ginis):
        ax.text(g + 0.001, bar.get_y() + bar.get_height() / 2,
                f"{g:.4f}", va="center", fontsize=8)
    ax.set_xlabel("Gini Coefficient", fontsize=11)
    ax.set_title(
        f"Intra-Regional Gini Coefficients @ {minutes}-min threshold\n"
        f"(Inequality of hospital access across districts within each state/region)",
        fontsize=11
    )
    ax.legend(fontsize=9)
    ax.grid(True, axis="x", alpha=0.3)
    red_patch   = mpatches.Patch(color="tomato",    label="Yangon Region")
    blue_patch  = mpatches.Patch(color="steelblue", label="Other states/regions")
    ax.legend(handles=[red_patch, blue_patch,
              mpatches.Patch(color="black", label=f"National Gini = {inter['gini']:.4f}")],
              fontsize=9)
    path2 = out_dir / f"gini_bar_{minutes}min.png"
    fig.tight_layout()
    fig.savefig(path2, dpi=150)
    plt.close(fig)
    print(f"  Saved: {path2}")

    # ── Plot 3: Gini vs threshold (Yangon + National) ────────────────────────
    matrix = multi_threshold_gini(adm1_rows, adm2_rows)
    fig, ax = plt.subplots(figsize=(9, 5))
    mins_x = [t // 60 for t in VALID_THRESHOLDS]

    highlight = ["Yangon", "Saigang", "Ayeyarwady", "Chin", "Mandalay"]
    cmap = plt.get_cmap("tab10")
    for i, state in enumerate(highlight):
        vals = [matrix[state].get(t, float("nan")) for t in VALID_THRESHOLDS]
        ax.plot(mins_x, vals, "o-", label=state, color=cmap(i), linewidth=2)

    nat_vals = [matrix["National"].get(t, float("nan")) for t in VALID_THRESHOLDS]
    ax.plot(mins_x, nat_vals, "s--", label="National", color="black",
            linewidth=2.5, markersize=7)

    ax.set_xlabel("Travel-time threshold (minutes)", fontsize=11)
    ax.set_ylabel("Gini Coefficient", fontsize=11)
    ax.set_title(
        "Intra-Regional Gini vs Travel-Time Threshold\n"
        "(Selected states/regions + national)", fontsize=12
    )
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    path3 = out_dir / "gini_vs_threshold.png"
    fig.tight_layout()
    fig.savefig(path3, dpi=150)
    plt.close(fig)
    print(f"  Saved: {path3}")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Myanmar Hospital Access Equity — Gini Coefficient Analysis"
    )
    parser.add_argument(
        "--threshold", type=int, default=3600,
        choices=VALID_THRESHOLDS, metavar="SECONDS",
        help="Travel-time threshold in seconds (default: 3600 = 60 min). "
             f"Choices: {VALID_THRESHOLDS}"
    )
    parser.add_argument(
        "--plot", action="store_true",
        help="Generate and save visualisation plots (requires matplotlib)."
    )
    parser.add_argument(
        "--out", type=Path, default=Path("output"),
        help="Output directory for plots (default: ./output)."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not DATA_FILE.exists():
        sys.exit(
            f"[ERROR] Data file not found: {DATA_FILE}\n"
            "        Place MMR_hospitals_access_wide.csv in the same directory "
            "as this script."
        )

    print(f"Loading data from: {DATA_FILE}")
    _, adm1_rows, adm2_rows = load_rows(DATA_FILE)
    print(f"  ADM1 records: {len(adm1_rows)}  |  ADM2 records: {len(adm2_rows)}")

    minutes = args.threshold // 60
    print(f"\nPrimary threshold: {args.threshold} s ({minutes} min)")

    # ── Compute ───────────────────────────────────────────────────────────────
    intra  = intra_regional_gini(adm2_rows, args.threshold)
    inter  = inter_regional_gini(adm1_rows, args.threshold)
    matrix = multi_threshold_gini(adm1_rows, adm2_rows)

    # ── Report ────────────────────────────────────────────────────────────────
    report_intra(intra, args.threshold)
    report_inter(inter, args.threshold)
    report_yangon_districts(intra)
    report_matrix(matrix)

    # ── Plots (optional) ──────────────────────────────────────────────────────
    if args.plot:
        print_section("VISUALISATIONS")
        plot_results(adm1_rows, adm2_rows, intra, inter, args.threshold, args.out)

    print("\nDone.")


if __name__ == "__main__":
    main()
