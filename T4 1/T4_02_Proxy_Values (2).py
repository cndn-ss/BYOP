# %% T4_02 — Proxy GR / RHOB / NPHI Values
# Builds the petrophysical proxy table for GLiM rock codes.
# All values are documented in PROXY_VALUES_README.md with full citations.
#
# Three sources:
#   GR   — Doveton (2017), KGS Geological Log Analysis, mineralogical reasoning
#   RHOB — Thomas & Ford (2007) via USGS SIR 2010-5070-C, Table 7-2
#   NPHI — Doveton (2017), KGS; mineralogical OH content reasoning
#   UCS  — Amadei (1996), citing Goodman (1989) and others; Hoek & Brown (1997)
#   comp — competency = UCS_avg / 360 MPa  (360 = max quartzite, Amadei Table 1)

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from scipy.stats import pearsonr

# ── CHANGE THIS ─────────────────────────────────────────────────────────
BASE_DIR = r"D:\Games_krish\T4 1"
# ────────────────────────────────────────────────────────────────────────

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_DIR    = os.path.join(BASE_DIR, "data", "outputs")
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# %%
# =============================================================
# PROXY VALUE TABLE
# See PROXY_VALUES_README.md for full derivation of every row.
# UCS reference max = 360 MPa (Amadei 1996, Table 1 quartzite max)
# MCT 'mt' values are weighted averages:
#   40% phyllite + 30% mica schist + 20% quartzite + 10% gneiss
#   (rock proportions from Valdiya 1980, Wadia Institute)
# =============================================================

UCS_REF_MAX = 360.0   # MPa — Amadei (1996) Table 1 quartzite maximum

proxy_data = {
    "rock_code": [
        "mt",   # MCT metamorphics — dominant rock in Joshimath corridor
        "pi",   # Acid/intermediate plutonics (granite, granodiorite)
        "pb",   # Basic plutonics (gabbro, amphibolite)
        "ss",   # Siliciclastic sedimentary (sandstone, arkose)
        "sc",   # Carbonate sedimentary (limestone, dolomite)
        "sm",   # Mixed sedimentary
        "su",   # Unconsolidated (alluvium, colluvium, slope debris)
        "va",   # Acid volcanics (rhyolite)
        "vb",   # Basic volcanics (basalt)
        "vi",   # Intermediate volcanics (andesite)
        "pa",   # Pyroclastics (tuff)
        "ev",   # Evaporites (gypsum)
        "wb",   # Water bodies
        "nd",   # No data (regional fallback)
        "ig",   # Ice/glaciers
        "ds",   # Dunes/sand
    ],

    # GR (API units) — Sources: Doveton 2017 (KGS), mineralogical K content
    # High K in micas → high GR for phyllite/schist
    # Near-zero K in quartz, chlorite → low GR for quartzite, gabbro
    # Granite ~220 API documented directly (Doveton 2017, Russell County well)
    "GR_api": [
        102,   # mt — weighted: 0.4×135 + 0.3×115 + 0.2×15 + 0.1×100 (see README)
        220,   # pi — documented ~220 API for granite (Doveton 2017)
         30,   # pb — basic, no K: "very low in basic igneous rocks" (Doveton 2017)
         80,   # ss — moderate K from feldspars
         25,   # sc — carbonate, very low radioactivity
         60,   # sm — average of ss and sc
         90,   # su — clay content raises GR; silty alluvium typical
        160,   # va — acid volcanic, high K
         35,   # vb — basalt, low GR (Doveton 2017)
         85,   # vi — intermediate between va and vb
        110,   # pa — pyroclastics variable; elevated from K in glass shards
         25,   # ev — gypsum/halite, no radioactive minerals
          0,   # wb — not rock
        102,   # nd — regional average (same as mt)
          0,   # ig — not rock
         55,   # ds — quartz-dominated sand, low K
    ],

    # RHOB (g/cm³) — Source: Thomas & Ford (2007) via USGS SIR 2010-5070-C Table 7-2
    # Quartzite 2.60, Schist 2.64, Phyllite 2.74, Gneiss 2.80, Amphibolite 2.96
    # Granite ~2.60 (Doveton 2017 borehole log)
    # Alluvium 1.90 (GW-Project 2020, wet bulk density unconsolidated)
    "RHOB_gcc": [
        2.69,  # mt — weighted: 0.4×2.74 + 0.3×2.64 + 0.2×2.60 + 0.1×2.80
        2.60,  # pi — granite, documented (Doveton 2017)
        2.96,  # pb — amphibolite value (USGS SIR Table 7-2)
        2.55,  # ss — sandstone, porous; slightly below quartz grain density
        2.71,  # sc — calcite grain density (Chemistry LibreTexts 2023)
        2.58,  # sm — average of ss and sc
        1.90,  # su — wet bulk density unconsolidated (GW-Project 2020)
        2.52,  # va — rhyolite, moderate density; vesicular
        2.90,  # vb — basalt; dense; Doveton 2017 "about 3.0 g/cc" for dense zones
        2.70,  # vi — andesite; between va and vb
        1.80,  # pa — tuff; highly vesicular, very low density
        2.32,  # ev — gypsum mineral density
        1.00,  # wb — water
        2.69,  # nd — regional average
        0.92,  # ig — ice density
        1.65,  # ds — loose sand
    ],

    # NPHI (fraction 0.0–1.0) — Source: Doveton (2017), KGS
    # Granite: ~1 unit (Doveton 2017: "about 1 limestone-equivalent unit")
    # Chlorite schist: ~0.50 ("Schlumberger tabulated: 52%", Doveton 2017)
    # Mica phyllite/schist: 0.18–0.25 (structural OH in muscovite/biotite)
    # Quartzite: ~0.01–0.03 (tight, no OH groups)
    # Rule: "low in silica-rich metamorphics, increased in micaceous rocks" (Doveton 2017)
    "NPHI": [
        0.16,  # mt — weighted: 0.4×0.22 + 0.3×0.18 + 0.2×0.02 + 0.1×0.10
        0.01,  # pi — granite "about 1 limestone-equivalent unit" ≈ 0.01 (Doveton 2017)
        0.05,  # pb — basic plutonics, tight
        0.15,  # ss — sandstone inter-granular porosity
        0.10,  # sc — carbonate, fracture/vug porosity
        0.13,  # sm — average ss and sc
        0.35,  # su — unconsolidated, high porosity
        0.08,  # va — rhyolite, variable vesicularity
        0.10,  # vb — basalt weathered "about 20 units" (Doveton 2017); /100 = 0.20
               #      but this is APPARENT porosity including alteration minerals
               #      fresh basalt ~0.05; using 0.10 as moderate estimate
        0.09,  # vi — intermediate
        0.30,  # pa — tuff, vesicular, high porosity
        0.15,  # ev — gypsum moderate
        1.00,  # wb — water
        0.16,  # nd — regional average
        1.00,  # ig — ice (100% hydrogen from ice lattice OH perspective)
        0.40,  # ds — loose sand with air/water-filled spaces
    ],

    # UCS_MPa — Uniaxial Compressive Strength
    # Source: Amadei (1996) Table 1 (n-sample averages, citing Goodman 1989 etc.)
    # Hoek & Brown (1997) Table 1 for field classification of phyllite, tuff
    # Phyllite: R4 = 50–100 MPa; use 40 MPa (conservative, foliation-parallel failure)
    "UCS_MPa": [
        108.0,  # mt — weighted: 0.4×40 + 0.3×57.8 + 0.2×288.8 + 0.1×174.4 = 108.1
        181.7,  # pi — granite average, Amadei (1996) Table 1, n=26
        214.1,  # pb — basalt average used as proxy for gabbro, Amadei (1996) n=16
         90.1,  # ss — sandstone average, Amadei (1996) Table 1, n=46
        120.9,  # sc — limestone average, Amadei (1996) Table 1, n=51
         90.0,  # sm — approximate (same as sandstone)
          5.0,  # su — near-zero; unconsolidated does not have UCS in strict sense
        100.0,  # va — estimate; rhyolite not in Amadei table; similar to limestone
        214.1,  # vb — basalt average, Amadei (1996) Table 1, n=16
        150.0,  # vi — interpolated between ss and vb
         25.0,  # pa — Hoek & Brown (1997): R3 "tuff" = 25–50 MPa; use lower bound
          5.0,  # ev — gypsum, very weak; Hoek R2 = 5–25 MPa
          0.0,  # wb — not rock
        108.0,  # nd — regional average
          0.0,  # ig — not rock
          5.0,  # ds — loose sand
    ],
}

df = pd.DataFrame(proxy_data)

# Derive competency from normalised UCS
df["competency"] = (df["UCS_MPa"] / UCS_REF_MAX).clip(0.0, 1.0).round(3)

print("Proxy table:")
print(df[["rock_code","GR_api","RHOB_gcc","NPHI","UCS_MPa","competency"]].to_string(index=False))

# %%
# --- Validate geophysical relationships ---
# High GR → weak rock (negative correlation with competency)
# High RHOB → strong rock (positive correlation)
# High NPHI → weak rock (negative correlation)

df_rocks = df[~df["rock_code"].isin(["wb","ig","nd"])].copy()
print("\nGeophysical consistency checks:")
for col, expected in [("GR_api","-"), ("RHOB_gcc","+"), ("NPHI","-")]:
    corr, _ = pearsonr(df_rocks[col], df_rocks["competency"])
    correct = (corr < 0 and expected == "-") or (corr > 0 and expected == "+")
    print(f"  corr({col:10s}, competency) = {corr:+.3f}  "
          f"[expected {expected}]  {'✓' if correct else '✗ CHECK VALUES'}")

# %%
# --- MCT zone calculation printout ---
print("\n--- MCT Zone Weighted Average ('mt') ---")
print("Proportions from Valdiya (1980):")
components = [
    ("Phyllite",    0.40,  40.0, 135, 2.74, 0.22),
    ("Mica Schist", 0.30,  57.8, 115, 2.64, 0.18),
    ("Quartzite",   0.20, 288.8,  15, 2.60, 0.02),
    ("Gneiss",      0.10, 174.4, 100, 2.80, 0.10),
]
w_comp = w_gr = w_rhob = w_nphi = 0
for rock, prop, ucs, gr, rhob, nphi in components:
    comp = ucs / UCS_REF_MAX
    w_comp += prop * comp
    w_gr   += prop * gr
    w_rhob += prop * rhob
    w_nphi += prop * nphi
    print(f"  {prop:.0%} {rock:15s}: UCS={ucs:5.1f} MPa → comp={comp:.3f}")

print(f"\n  Weighted competency : {w_comp:.3f}")
print(f"  Weighted GR         : {w_gr:.1f} API")
print(f"  Weighted RHOB       : {w_rhob:.3f} g/cm³")
print(f"  Weighted NPHI       : {w_nphi:.3f}")

# %%
# --- Plot ---
plot_df = df[~df["rock_code"].isin(["wb","ig","nd","ds"])].copy()
plot_df = plot_df.sort_values("competency", ascending=True)
colors  = plt.cm.RdYlGn(plot_df["competency"].values)

fig, axes = plt.subplots(1, 3, figsize=(17, 6))
fig.suptitle("Proxy Petrophysical Values by GLiM Rock Code\n"
             "GR: Doveton 2017 | RHOB: USGS SIR 2010-5070-C | UCS: Amadei 1996",
             fontsize=11)

for ax, (col, xlabel) in zip(axes, [
    ("GR_api",   "Gamma Ray (API)"),
    ("RHOB_gcc", "Bulk Density (g/cm³)"),
    ("NPHI",     "Neutron Porosity"),
]):
    bars = ax.barh(plot_df["rock_code"], plot_df[col],
                   color=colors, edgecolor="black", linewidth=0.4)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", alpha=0.3)
    for bar, val in zip(bars, plot_df[col]):
        ax.text(bar.get_width()*0.5, bar.get_y()+bar.get_height()/2,
                f"{val:.2f}", ha="center", va="center", fontsize=7)

sm = ScalarMappable(cmap="RdYlGn", norm=Normalize(vmin=0, vmax=1))
sm.set_array([])
fig.colorbar(sm, ax=axes, fraction=0.015, pad=0.04,
             label="Competency (0=Weak, 1=Strong)")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR,"proxy_values.png"), dpi=150, bbox_inches="tight")
plt.show()

# %%
# --- Save ---
out_path = os.path.join(PROCESSED_DIR, "proxy_values_lookup.csv")
df.to_csv(out_path, index=False)
print(f"Saved: {out_path}")
