# Proxy Petrophysical Values — Scientific Derivation & References
## T4 GeoSentinel+ | Lithological Proxy Transfer Framework

---

## Purpose

The competency model (T3) was trained on Norwegian well log data (FORCE 2020).
It predicts rock competency from three wireline log measurements:
- **GR** — Gamma Ray (API units)
- **RHOB** — Bulk Density (g/cm³)
- **NPHI** — Neutron Porosity (fraction)

No wells exist in the Joshimath corridor. We cannot measure these logs directly.
This document derives **proxy values** — scientifically grounded estimates of
what GR, RHOB, and NPHI a given rock type would produce if drilled — from
published petrophysical compilations and mineralogical first principles.

---

## Method: UCS-Normalised Competency

Competency (0–1) is derived by normalising Uniaxial Compressive Strength (UCS):

```
competency = UCS_average / UCS_reference_max
```

where `UCS_reference_max = 360 MPa` (maximum quartzite value, Amadei 1996 Table 1).

This gives a physically grounded, dimensionless strength index. Values are
clipped to [0, 1]. Foliation anisotropy is accounted for by using the average
UCS from multi-direction test compilations, which implicitly includes
along-foliation weakness.

---

## Source 1: UCS Compilation — Amadei (1996)

**Citation:**
> Amadei, B. (1996). *Strength Properties of Rocks and Rock Masses*.
> CVEN 5768 Lecture Notes 8, University of Colorado Boulder.
> Citing primary sources: Balmer (1953), Johnson & DeGraff (1988),
> Hatheway & Kiersch (1989), Goodman (1989).
> URL: https://ceae.colorado.edu/~amadei/CVEN5768/PDF/NOTES8.pdf

**Extracted Table 1 — Uniaxial Compressive Strength (MPa):**

| Rock Type | n samples | Min | Average | Max |
|-----------|-----------|-----|---------|-----|
| Granite   | 26 | 48.8 | 181.7 | 324.0 |
| Basalt    | 16 | 104.8 | 214.1 | 358.6 |
| Gneiss    | 24 | 84.5 | 174.4 | 251.0 |
| Schist    | 17 | 8.0 | 57.8 | 165.6 |
| Quartzite | 7 | 214.9 | 288.8 | 359.0 |
| Marble    | 9 | 62.0 | 120.5 | 227.6 |
| Limestone | 51 | 35.3 | 120.9 | 373.0 |
| Sandstone | 46 | 10.0 | 90.1 | 235.2 |
| Shale     | 14 | 34.3 | 103.0 | 231.0 |

**Note on Phyllite:** Not listed separately in Amadei. Classified R4
(50–100 MPa) by Hoek & Brown (1997) field strength classification.
Himalayan phyllite fails preferentially along foliation planes — along-foliation
UCS as low as 8–25 MPa is documented for mica-phyllite (Vermont Transportation
Agency, 2015). We adopt 40 MPa as conservative mean for foliation-parallel failure.

**Note on Alluvium (su):** Not a rock. UCS ≈ 0–5 MPa (clastic unconsolidated
material). We set competency = 0.05 as a non-zero minimum to avoid model issues
with zero values.

---

## Source 2: Rock Density — USGS SIR 2010-5070-C

**Citation:**
> Thomas, M.D., Oneschuk, D., and Ford, K.L. (2000, 2007), compiled in:
> Lisa A. Morgan et al. (2010). *Geophysical Characteristics of Volcanogenic
> Massive Sulfide Deposits*. USGS Scientific Investigations Report 2010-5070-C,
> Chapter 7, Table 7-2.
> URL: https://pubs.usgs.gov/sir/2010/5070/c/Chapter7SIR10-5070-C-3.pdf

**Extracted density values for metamorphic rocks (g/cm³):**

| Rock Type | Density (g/cm³) |
|-----------|----------------|
| Quartzite | 2.60 |
| Schist | 2.64 |
| Gneiss | 2.80 |
| Amphibolite | 2.96 |
| Phyllite | 2.74 |
| Chlorite Schist | 2.87 |
| Marble | 2.75 |

**Supplementary density values** from Britannica / Chemistry LibreTexts (2023):
- Limestone: 2.71 g/cm³ (calcite grain density)
- Dolomite: 2.85 g/cm³
- Quartz mineral: 2.65 g/cm³
- Granite: 2.60–2.70 g/cm³ (KGS documented ~2.60 from borehole log)

**Note on alluvium:** Wet bulk density of unconsolidated sediments is 1.7–2.1
g/cm³ depending on saturation and compaction. We use 1.90 g/cm³ as a
representative value for saturated slope debris (GW-Project, 2020).

---

## Source 3: Gamma Ray Log Interpretation — KGS Geological Log Analysis

**Citation:**
> Doveton, J.H. (2017). *Geological Log Analysis: Igneous and Metamorphic Rocks*.
> Kansas Geological Survey, University of Kansas.
> URL: https://www.kgs.ku.edu/Publications/Bulletins/LA/09_igneous.html
> (web publication, placed online March 24, 2017)

**Key statements from source (paraphrased):**
- Acid igneous rocks (granites, rhyolites): **very high GR** (~220 API documented
  from borehole in Russell County, Kansas)
- Basic igneous rocks (gabbros, basalts): **very low GR**
- Metamorphic rocks: **typically low GR**, except those with significant
  potassium feldspar content
- Chlorite schist: **very low radioactivity** (consistent with metamorphism of
  basic igneous rocks; chlorite has no K)

**Mineralogical derivation for Himalayan mica-metamorphics:**
Himalayan phyllite and schist in the MCT zone are mica-dominated (muscovite
KAl₂(AlSi₃O₁₀)(OH)₂ and biotite K(Mg,Fe)₃(AlSi₃O₁₀)(OH)₂). Both contain
significant K, making them more radioactive than chlorite schist but less than
pure granite. We estimate GR using the radioactivity rule from KGS:

```
GR contribution ∝ 4×Th(ppm) + 8×U(ppm) + 16×K(%)  [API unit formula]
```

For muscovite mica: K content ~9–10% by weight → significant GR contribution.
For comparison: typical K-rich shale (a proxy for mica-rich rock) runs 80–150 API.

**Derived GR estimates for MCT-zone rocks:**
- Phyllite (muscovite + chlorite + quartz): ~120–150 API (K from muscovite)
- Mica schist (muscovite + biotite): ~100–130 API (K from both micas)
- Quartzite (near-pure SiO₂): ~10–20 API (no radioactive minerals)
- Gneiss (mixed mineralogy): ~80–120 API (variable K-feldspar content)
- Granite: ~200–240 API (Doveton 2017: ~220 API documented)
- Gabbro/basalt: ~20–45 API (mafic, no K)

---

## Source 4: Neutron Porosity — KGS Geological Log Analysis

**Citation:** Same as Source 3 (Doveton 2017).

**Key statements from source:**
- Granite: neutron porosity **~1 limestone-equivalent unit** (extremely low, tight)
- Chlorite schist: neutron porosity **~50 units** (exceptionally high due to
  bound OH in chlorite formula (Fe,Mg,Al)₆(Si,Al)₄O₁₀(OH)₈; Schlumberger
  pure chlorite table value cited as 52%)
- Basaltic lavas: neutron porosity **~20 units** (moderate, hydrothermal alteration)
- Metamorphic rocks: "low values in silica-rich metamorphics but **increased
  values in micaceous rocks** and **very high values in chlorite schists**"

**Derivation for Himalayan mica-metamorphics:**
Himalayan phyllite and schist contain significant OH-bearing micas (muscovite,
biotite, chlorite). OH groups register as apparent porosity on neutron logs.
- Muscovite: 4.5 wt% structural OH → NPHI contribution ~0.15
- Biotite: 3.7 wt% structural OH → NPHI contribution ~0.12
- Chlorite: much higher OH → NPHI 0.40–0.52 (Doveton 2017)
- Quartzite: no OH, tight → NPHI ~0.01–0.03

For MCT phyllite (muscovite-dominant): NPHI ~0.18–0.25
For mica schist (muscovite + biotite): NPHI ~0.15–0.22
For quartzite: NPHI ~0.01–0.05
For gneiss (mixed): NPHI ~0.08–0.14

---

## Source 5: Rock Strength Classification — Hoek & Brown (1997)

**Citation:**
> Hoek, E. and Brown, E.T. (1997). *Practical Estimates of Rock Mass Strength*.
> International Journal of Rock Mechanics and Mining Sciences, 34(8), 1165–1186.
> URL: https://www.rocscience.com/assets/resources/learning/hoek/
>       1997-Practical-Estimates-of-Rock-Mass-Strength.pdf

**Field strength classification (Table 1 of source):**

| Grade | Term | UCS (MPa) | Examples |
|-------|------|-----------|---------|
| R6 | Extremely Strong | >250 | Fresh basalt, chert, diabase, gneiss, granite, quartzite |
| R5 | Very Strong | 100–250 | Amphibolite, sandstone, basalt, gabbro, gneiss, granodiorite, limestone, marble, rhyolite, tuff |
| R4 | Strong | 50–100 | Limestone, marble, phyllite, sandstone, schist, shale |
| R3 | Medium Strong | 25–50 | Claystone, coal, concrete, schist, shale, siltstone |
| R2 | Weak | 5–25 | Chalk, rocksalt, potash |

This confirms: phyllite R4 (50–100 MPa), schist spanning R3–R4 (25–100 MPa),
quartzite R6 (>250 MPa). Note gneiss appears in both R5 and R6 depending
on whether fresh or weathered.

---

## MCT Zone Weighted Average Calculation (for GLiM code 'mt')

The Joshimath corridor lies on the Main Central Thrust (MCT), a major tectonic
structure separating Lesser Himalaya from Higher Himalaya.

**Rock proportion estimate for MCT zone in Chamoli District:**
Based on: Valdiya, K.S. (1980). *Geology of Kumaun Lesser Himalaya*.
Wadia Institute of Himalayan Geology, Dehradun. (Widely cited regional reference)

| Rock Type | Proportion | UCS avg (MPa) | Source | Competency |
|-----------|-----------|---------------|--------|-----------|
| Phyllite | 40% | 40 MPa (conservative for foliation-parallel) | Hoek & Brown 1997 | 0.11 |
| Mica Schist | 30% | 57.8 MPa | Amadei 1996, Table 1 | 0.16 |
| Quartzite | 20% | 288.8 MPa | Amadei 1996, Table 1 | 0.80 |
| Gneiss | 10% | 174.4 MPa | Amadei 1996, Table 1 | 0.48 |

**Weighted competency for 'mt':**
```
competency_mt = 0.40×0.11 + 0.30×0.16 + 0.20×0.80 + 0.10×0.48
             = 0.044 + 0.048 + 0.160 + 0.048
             = 0.300
```

**Weighted GR for 'mt':**
```
GR_mt = 0.40×135 + 0.30×115 + 0.20×15 + 0.10×100
      = 54 + 34.5 + 3 + 10
      = 101.5 ≈ 102 API
```

**Weighted RHOB for 'mt':**
```
RHOB_mt = 0.40×2.74 + 0.30×2.64 + 0.20×2.60 + 0.10×2.80
        = 1.096 + 0.792 + 0.520 + 0.280
        = 2.688 ≈ 2.69 g/cm³
```

**Weighted NPHI for 'mt':**
```
NPHI_mt = 0.40×0.22 + 0.30×0.18 + 0.20×0.02 + 0.10×0.10
        = 0.088 + 0.054 + 0.004 + 0.010
        = 0.156 ≈ 0.16
```

---

## Final Proxy Table

Normalisation reference: `UCS_max = 360 MPa` (max quartzite, Amadei 1996 Table 1)

| GLiM Code | Description | GR (API) | RHOB (g/cm³) | NPHI | UCS (MPa) | Competency | Primary Source |
|-----------|-------------|----------|--------------|------|-----------|-----------|----------------|
| mt | MCT metamorphics (weighted) | 102 | 2.69 | 0.16 | 108 | 0.30 | Valdiya 1980; Amadei 1996; Doveton 2017; USGS SIR 2010-5070-C |
| pi | Acid/int. plutonics (granite) | 220 | 2.60 | 0.01 | 181.7 | 0.50 | Doveton 2017 (GR); Amadei 1996 (UCS); USGS SIR (density) |
| pb | Basic plutonics (gabbro) | 30 | 2.96 | 0.05 | 214.1 | 0.59 | Doveton 2017 (GR, low in basic); Amadei 1996 basalt (UCS); USGS SIR (density) |
| ss | Siliciclastic sedimentary | 80 | 2.55 | 0.15 | 90.1 | 0.25 | Amadei 1996 (sandstone); KGS gamma-ray guide |
| sc | Carbonate sedimentary | 25 | 2.71 | 0.10 | 120.9 | 0.34 | Amadei 1996 (limestone); Chemistry LibreTexts density |
| sm | Mixed sedimentary | 70 | 2.58 | 0.14 | 90.0 | 0.25 | Average of ss and sc |
| su | Unconsolidated sediments | 90 | 1.90 | 0.35 | ~5 | 0.05 | GW-Project 2020 (density); near-zero UCS |
| va | Acid volcanics (rhyolite) | 160 | 2.52 | 0.08 | 100.0 | 0.28 | Doveton 2017 (high GR acid); moderate UCS estimate |
| vb | Basic volcanics (basalt) | 35 | 2.90 | 0.10 | 214.1 | 0.59 | Doveton 2017 (low GR basic); Amadei 1996 basalt |
| vi | Int. volcanics (andesite) | 85 | 2.70 | 0.09 | 150.0 | 0.42 | Interpolated between va and vb |
| pa | Pyroclastics (tuff) | 110 | 1.80 | 0.30 | 25.0 | 0.07 | Low UCS (weak, vesicular); moderate GR |
| ev | Evaporites (gypsum) | 30 | 2.32 | 0.15 | 10.0 | 0.03 | Very low UCS; low GR (no K) |
| wb | Water body | 0 | 1.00 | 1.00 | 0 | 0.00 | Not rock |
| ig | Ice/glaciers | 0 | 0.92 | 1.00 | 0 | 0.00 | Not rock |
| nd | No data | 102 | 2.69 | 0.16 | 108 | 0.30 | Regional average (same as mt) |
| ds | Dunes/sand | 55 | 1.65 | 0.40 | 5.0 | 0.01 | Loose sand, very weak |

---

## Limitations and Honest Caveats

1. **No direct measurements exist for Joshimath.** All values are proxies derived
   from global compilations. Actual values at any given outcrop will differ.

2. **GLiM resolution:** GLiM cannot distinguish phyllite from quartzite within the
   `mt` code. The weighted average of 0.30 is more conservative than pure
   quartzite (0.80) and more realistic for the MCT zone where phyllite dominates.

3. **GR values for metamorphics are uncertain.** KGS Doveton (2017) provides
   the directional rule (low except K-feldspar-bearing) but not a precise API
   number for every metamorphic subtype. Our estimates use mineralogical K content
   as a proxy for GR and are consistent with the directional rule.

4. **T3's model was trained on sedimentary sequences** (FORCE 2020 = Norwegian
   North Sea wells). Its learned patterns may not extrapolate cleanly to metamorphic
   rocks. This is documented as a project limitation.

5. **UCS from lab core ≠ field-scale rock mass strength.** Amadei's compilation
   is for intact core samples under confining pressure. In-situ rock mass strength
   is lower due to fractures, weathering, and foliation. The normalised competency
   score should be interpreted as a relative index, not an absolute strength.

---

## Full Reference List

1. Amadei, B. (1996). Strength Properties of Rocks and Rock Masses. CVEN 5768 Lecture Notes, University of Colorado Boulder.

2. Doveton, J.H. (2017). Geological Log Analysis — Igneous and Metamorphic Rocks. Kansas Geological Survey, University of Kansas. https://www.kgs.ku.edu/Publications/Bulletins/LA/09_igneous.html

3. Hoek, E. and Brown, E.T. (1997). Practical Estimates of Rock Mass Strength. International Journal of Rock Mechanics and Mining Sciences, 34(8), 1165–1186. https://www.rocscience.com/assets/resources/learning/hoek/1997-Practical-Estimates-of-Rock-Mass-Strength.pdf

4. Thomas, M.D. and Ford, K.L. (2007), compiled in: Morgan, L.A. et al. (2010). Geophysical Characteristics of Volcanogenic Massive Sulfide Deposits. USGS Scientific Investigations Report 2010-5070-C, Chapter 7. https://pubs.usgs.gov/sir/2010/5070/c/Chapter7SIR10-5070-C-3.pdf

5. Valdiya, K.S. (1980). Geology of Kumaun Lesser Himalaya. Wadia Institute of Himalayan Geology, Dehradun, 291 pp.

6. GW-Project Authors (2020). Hydrogeologic Properties of Earth Materials and Principles of Groundwater Flow. The Groundwater Project, Guelph, Ontario. https://books.gw-project.org/hydrogeologic-properties-of-earth-materials-and-principles-of-groundwater-flow/chapter/density-of-common-minerals-rock-types-and-soils/

7. Vermont Agency of Transportation (2015). Unconfined Compressive Strength of Vermont Rock. Materials and Research Section, VTrans, Montpelier, Vermont.

8. Hartmann, J. and Moosdorf, N. (2012). The new global lithological map database GLiM: A representation of rock properties at the Earth's surface. Geochemistry, Geophysics, Geosystems, 13, Q12004. https://doi.org/10.1029/2012GC004370
