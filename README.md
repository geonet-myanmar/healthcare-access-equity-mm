# Myanmar Hospital Access Equity Analysis

A Python analysis of inequality in hospital accessibility across Myanmar's 14 states and regions, using population-weighted **Gini coefficients** derived from OpenStreetMap travel-time accessibility data.

---

## Table of Contents

- [Overview](#overview)
- [Data Source](#data-source)
- [Repository Structure](#repository-structure)
- [Methodology](#methodology)
- [Results](#results)
  - [National (Inter-Regional) Gini](#national-inter-regional-gini)
  - [Intra-Regional Gini — Yangon vs All States](#intra-regional-gini--yangon-vs-all-states)
  - [Yangon District Breakdown](#yangon-district-breakdown)
  - [Sensitivity to Travel-Time Threshold](#sensitivity-to-travel-time-threshold)
- [Interpretation](#interpretation)
- [Installation & Usage](#installation--usage)
- [License](#license)

---

## Overview

Healthcare access in Myanmar is highly unequal. This project quantifies *how* unequal — both **between** states/regions (inter-regional inequality) and **within** each state across its districts (intra-regional inequality) — using the Gini coefficient as a standardised measure of distributional inequality applied to hospital accessibility rates.

**Key questions answered:**
1. Which states and regions have the most unequal distribution of hospital access within their own borders?
2. How does Yangon Region compare with the rest of Myanmar?
3. How does inequality change depending on the travel-time threshold chosen?

---

## Data Source

| Field | Detail |
|---|---|
| **Provider** | OpenStreetMap via [HOT Raw Data API](https://github.com/hotosm/raw-data-api) |
| **Export date** | 2026-02-12 |
| **File used** | `MMR_hospitals_access_wide.csv` |
| **License** | [Open Database License (ODbL) 1.0](http://opendatacommons.org/licenses/odbl/1.0/) |
| **Coverage** | Myanmar — national (ADM0), 14 states/regions (ADM1), 74 districts (ADM2) |

The dataset records, for each administrative unit at each travel-time threshold (10–120 min in 10-min steps), the **share of the population** that can reach a hospital within that time. Population sub-groups (under-5, school-age, adults, women of childbearing age, elderly) are also provided; this analysis uses the **total population** share.

---

## Repository Structure

```
geonet/
├── analysis.py                      # Main analysis script
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── MMR_hospitals_access_wide.csv    # Primary dataset (ADM0/1/2, wide format)
├── MMR_hospitals_access_long.csv    # Same data, long format
├── MMR_primary_healthcare_access_wide.csv
├── MMR_primary_healthcare_access_long.csv
├── MMR_education_access_wide.csv
├── MMR_education_access_long.csv
└── hotosm_mmr_education_facilities_points_geojson.geojson
```

> **Note:** `output/` (generated plots) is git-ignored; it is created by `--plot`.

---

## Methodology

### Travel-time thresholds

The dataset encodes cumulative hospital accessibility at 12 travel-time thresholds:

| Threshold (s) | Minutes |
|---|---|
| 600 | 10 |
| 1200 | 20 |
| … | … |
| 3600 | **60** ← primary threshold used |
| … | … |
| 7200 | 120 |

A 60-minute travel time is the standard benchmark used by the WHO and public-health literature for gauging hospital accessibility in low- and middle-income countries.

### Gini coefficient (population-weighted Lorenz curve)

For a set of administrative units each with population *p_i* and accessibility rate *a_i* (% of population within threshold of a hospital):

1. **Sort** units by *a_i* ascending (least-served first).
2. **Compute** the accessible population for each unit: *w_i = p_i × a_i / 100*.
3. **Build the Lorenz curve** — plot cumulative population share (*x_k*) against cumulative accessible-population share (*y_k*).
4. **Integrate** the area under the Lorenz curve using the trapezoid rule.
5. **Gini = 1 − 2 × (area under Lorenz curve)**.

A Gini of **0** indicates every district has an identical access rate (perfect equality). A Gini of **1** indicates that all accessible population is concentrated in a single unit (perfect inequality).

### Two levels of analysis

| Analysis | Unit of observation | Population grouped by |
|---|---|---|
| **Intra-regional** | ADM2 districts | Parent ADM1 state/region |
| **Inter-regional (national)** | ADM1 states/regions | Country |

The 74 ADM2 districts are assigned to their 14 parent ADM1 states/regions via a hard-coded geographic lookup table (`DISTRICT_TO_STATE` in `analysis.py`), validated against Myanmar's official administrative divisions.

---

## Results

All results below use the **60-minute travel-time threshold** unless stated otherwise.

### National (Inter-Regional) Gini

```
National Gini = 0.0524
```

| Rank | State / Region | Access Rate | Population |
|------|---------------|------------|------------|
| 1 (worst) | Chin          | 58.49% | 0.31M |
| 2  | Saigang (Sagaing) | 74.43% | 4.28M |
| 3  | Rakhine       | 76.44% | 1.51M |
| 4  | Kachin        | 76.86% | 1.53M |
| 5  | Tanitharyi    | 82.37% | 1.21M |
| 6  | Ayeyarwady    | 83.07% | 5.31M |
| 7  | Magway        | 85.95% | 3.38M |
| 8  | Shan          | 86.23% | 5.91M |
| 9  | Kayin         | 93.96% | 1.53M |
| 10 | Mandalay      | 94.62% | 6.52M |
| 11 | Mon           | 95.99% | 1.91M |
| 12 | Bago          | 96.45% | 5.03M |
| 13 | Kayah         | 96.82% | 0.31M |
| **14 (best)** | **Yangon** | **98.64%** | **8.92M** |

The 40-percentage-point gap between Chin State (58.49%) and Yangon (98.64%) drives the national Gini.

---

### Intra-Regional Gini — Yangon vs All States

Inequality of hospital access across districts *within* each state/region:

| State/Region | Gini | Districts | Mean weighted access |
|---|---|---|---|
| Saigang | **0.0849** | 11 | 74.43% |
| Ayeyarwady | 0.0823 | 6 | 83.07% |
| Rakhine | 0.0655 | 5 | 76.44% |
| Shan | 0.0521 | 14 | 86.23% |
| Tanitharyi | 0.0511 | 3 | 82.37% |
| Kachin | 0.0456 | 4 | 76.86% |
| Chin | 0.0357 | 3 | 58.49% |
| Mandalay | 0.0310 | 7 | 94.62% |
| Magway | 0.0287 | 5 | 85.95% |
| Kayin | 0.0134 | 4 | 93.96% |
| Bago | 0.0096 | 4 | 96.45% |
| **Yangon** | **0.0071** | 4 | 98.64% |
| Kayah | 0.0011 | 2 | 96.82% |
| Mon | 0.0005 | 2 | 95.99% |

**Yangon's intra-regional Gini of 0.0071 ranks 3rd lowest (most equitable) among all 14 divisions.** The two lower values (Kayah, Mon) each have only 2 districts, making them less meaningful comparators.

---

### Yangon District Breakdown

| District | Access @ 60 min | Population |
|---|---|---|
| Yangon (South) | 96.65% | 1.672M |
| Yangon (North) | 97.98% | 3.152M |
| Yangon (East) | 100.00% | 2.894M |
| Yangon (West) | 100.00% | 1.198M |

All four districts exceed 96% coverage. The small residual Gini (0.0071) is attributable to Yangon South's marginal 3.35% gap versus the fully covered eastern and western zones.

---

### Sensitivity to Travel-Time Threshold

Gini coefficients at every threshold for selected states and the national level:

```
State/Region    10m    20m    30m    40m    50m    60m    70m    80m   120m
────────────────────────────────────────────────────────────────────────────
Saigang        0.187  0.158  0.132  0.107  0.094  0.085  0.087  0.082  0.073
Ayeyarwady     0.135  0.127  0.118  0.102  0.092  0.082  0.071  0.069  0.056
Rakhine        0.118  0.103  0.093  0.082  0.065  0.066  0.061  0.057  0.052
Kachin         0.124  0.078  0.072  0.059  0.051  0.046  0.045  0.043  0.035
Shan           0.103  0.087  0.075  0.059  0.054  0.052  0.049  0.043  0.025
Mandalay       0.167  0.097  0.071  0.049  0.035  0.031  0.029  0.021  0.008
Magway         0.052  0.042  0.028  0.030  0.029  0.029  0.028  0.026  0.018
Tanitharyi     0.022  0.050  0.050  0.048  0.050  0.051  0.041  0.038  0.038
Chin           0.070  0.029  0.024  0.026  0.036  0.036  0.023  0.015  0.020
Bago           0.053  0.033  0.024  0.016  0.012  0.010  0.009  0.008  0.004
Kayin          0.062  0.036  0.035  0.024  0.017  0.013  0.013  0.012  0.014
Yangon         0.079  0.052  0.039  0.027  0.012  0.007  0.005  0.004  0.002
Kayah          0.000  0.018  0.001  0.002  0.001  0.001  0.001  0.000  0.000
Mon            0.003  0.003  0.001  0.002  0.000  0.001  0.001  0.002  0.000
────────────────────────────────────────────────────────────────────────────
National       0.148  0.103  0.081  0.067  0.059  0.052  0.046  0.043  0.034
```

At a **10-minute** threshold, Yangon's intra-regional Gini (0.079) appears relatively high because peripheral sub-districts lack hospitals within a 10-minute radius. As the threshold expands to **60 minutes**, Yangon's Gini collapses to near zero — all districts achieve near-full coverage. This demonstrates that Yangon's hospital *density* is high but not perfectly uniform at fine spatial scales.

---

## Interpretation

### Core–periphery divide is the dominant driver

The national Gini (0.052) **exceeds** the intra-regional Gini of most individual states. This means inequality *between* states is greater than inequality *within* them — a classic core–periphery pattern where Yangon and the central corridor are well-served while mountainous border states (Chin, Kachin, Rakhine) lag far behind.

### Yangon: high access, high equity

Yangon is Myanmar's best-served region on both dimensions:
- **Highest access rate** nationally (98.64% within 60 min).
- **Near-uniform internal distribution** (Gini = 0.0071).

This reflects the concentration of Myanmar's healthcare infrastructure in the commercial capital, including large government referral hospitals, private hospitals, and specialist clinics.

### Most inequitable states internally

- **Saigang (Sagaing) Region** — 11 districts spanning vast terrain from the Chindwin River valley to remote upland areas; some districts are well-connected while others are extremely isolated.
- **Ayeyarwady Region** — the Irrawaddy Delta geography creates uneven access; waterway communities in districts like Labutta and Pyapon face physical barriers.
- **Rakhine State** — a combination of coastal isolation, conflict-affected zones (especially Maungdaw), and limited road infrastructure creates steep within-state disparities.

### Policy implication

Priority interventions should target:
1. **Between-region gaps**: Build or upgrade hospitals in Chin State, remote Saigang districts, and Rakhine State, where a large share of the population cannot reach a hospital within 60 minutes.
2. **Within-region hotspots**: Focus on remote districts within Saigang (Hkamti, Tamu), Ayeyarwady (Labutta), and Kachin (Puta-O) where intra-regional disparity is driven by geographic isolation.
3. **Mobile and telemedicine infrastructure**: For communities beyond the practical reach of fixed-facility investment, mobile health units and telemedicine can reduce functional inequality without requiring new hospital construction.

---

## Installation & Usage

### Requirements

- Python 3.9+
- No third-party packages required for the core analysis
- `matplotlib >= 3.7` required only for the optional `--plot` flag

```bash
# Install optional visualisation dependency
pip install matplotlib
```

### Basic usage

```bash
# Run with default 60-minute threshold
python analysis.py

# Run with a different threshold (e.g., 30 minutes)
python analysis.py --threshold 1800

# Run and generate plots (saved to ./output/)
python analysis.py --plot

# Run with custom threshold and custom output directory
python analysis.py --threshold 1800 --plot --out results/plots
```

### Command-line arguments

| Argument | Default | Description |
|---|---|---|
| `--threshold` | `3600` | Travel-time threshold in **seconds**. Must be one of the 12 valid values (600 … 7200). |
| `--plot` | off | Generate and save Lorenz curve, bar chart, and threshold-sensitivity plots. |
| `--out` | `./output` | Directory where plot images are saved. |

### Output

The script prints four sections to stdout:

1. **Intra-regional Gini** — one row per state/region, sorted by Gini descending.
2. **Inter-regional (national) Gini** — country-level summary with all 14 regions ranked by access rate.
3. **Yangon district breakdown** — access rates and populations for the four Yangon districts.
4. **Full Gini matrix** — every state at every threshold.

When `--plot` is used, three PNG files are written to `--out`:

| File | Content |
|---|---|
| `lorenz_national_Xmin.png` | National Lorenz curve with region labels |
| `gini_bar_Xmin.png` | Horizontal bar chart of intra-regional Ginis |
| `gini_vs_threshold.png` | Line chart of Gini vs threshold for selected states |

---

## License

**Code**: MIT License — see `LICENSE` file (add one before publishing).

**Data**: The underlying OpenStreetMap data is licensed under the
[Open Database License (ODbL) 1.0](http://opendatacommons.org/licenses/odbl/1.0/).
Individual database contents are licensed under the
[Database Contents License (DbCL) 1.0](http://opendatacommons.org/licenses/dbcl/1.0/).
Any derived works using this data must comply with the ODbL share-alike requirement.

© OpenStreetMap contributors
