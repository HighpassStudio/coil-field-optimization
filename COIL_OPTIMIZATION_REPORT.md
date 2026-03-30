# Magnetic Coil Geometry Optimization for Field Uniformity Per Watt

**Author:** Brad Loomis (MS, PE, PTOE)
**Date:** 2026-03-29
**Status:** Steps 1-3 complete (model, metric, geometry comparison). Seeking peer review before bench testing.
**Code:** `coil_optimization.py` (Python, ~500 lines, numpy + matplotlib only)

---

## Problem Statement

Optimizing coil geometries for field uniformity under power and thermal constraints is a well-studied problem, with published work spanning decades (Lee-Whiting 1957, Merritt 1983, Zhu 2022 multi-objective optimization, Nieves 2019 conical coils). This project does not claim to fill a major gap in the literature.

What this project does: build an accessible, open-source tool that applies a practical composite metric (field uniformity per watt) across multiple coil geometries, with the explicit goal of physical bench validation. The value is in reproducibility and accessibility, not novelty of the underlying physics.

**Practical question:** Given a power budget and a target volume, which standard coil geometry performs best -- and can a simple home-lab setup validate the simulation?

---

## Step 1: Biot-Savart Field Solver

### Method

Discrete Biot-Savart integration over wire segments:

```
dB = (mu_0 / 4*pi) * I * (dl x r_hat) / r^2
```

Each coil geometry is discretized into ordered (x, y, z) points. Adjacent points define current-carrying segments. The field at each sample point is the vector sum of contributions from all segments.

Wire resistance computed from geometry:

```
R = rho_copper * wire_length / wire_cross_section_area
P = I^2 * R
```

### Validation

Tested against the exact analytical solution for a Helmholtz pair:

```
B_z(on-axis) = mu_0 * N * I * R^2 / (2 * (R^2 + z^2)^(3/2))
```

Summed for two coils at z = +/- R/2.

| Test | Expected | Got | Error |
|------|----------|-----|-------|
| Center field (z=0), R=5cm, I=1A, N=10 | 179.84 uT | 179.85 uT | 0.01% |
| On-axis profile (21 points, z = -R to +R) | analytical curve | numerical curve | 0.01% max |

**Verdict:** Solver is correct to within numerical discretization error.

---

## Step 2: Figure of Merit

### Definition

```
F = B_avg / (sigma_B * P)
```

Where:
- **B_avg** = mean field magnitude over the target volume (T)
- **sigma_B** = standard deviation of field magnitude over the target volume (T)
- **P** = resistive power dissipation in the coil (W)

**Units:** 1/W (higher is better)

**Interpretation:** How much average field you get per unit of field variation per unit of power dissipated. A coil with high F produces a strong, uniform field without wasting energy as heat.

### Why this metric

- **B_avg / sigma_B** alone (without P) would just measure uniformity -- it would favor massive coils with many turns regardless of power.
- **Dividing by P** penalizes designs that achieve uniformity through brute-force current.
- The metric naturally favors geometries that are efficient: fewer turns, lower resistance, but still uniform.

### Sanity checks

The metric correctly handles edge cases:
- Perfect uniformity (sigma_B = 0) gives F = infinity -- as expected, a perfectly uniform field at any power is ideal.
- Zero field (B_avg = 0) gives F = 0 -- correct, no field means no useful coil.
- Higher power at same uniformity gives lower F -- correct, more power for same result is worse.
- The metric does not produce nonsense rankings (see Step 3 results).

### Alternative metrics considered

| Metric | Formula | Why not chosen |
|--------|---------|---------------|
| Uniform volume per watt | V(< threshold) / P | Requires arbitrary threshold choice |
| RMS error per watt | (1/P) * sqrt(mean((B - B_avg)^2)) / B_avg | Equivalent to sigma_B / (B_avg * P) = 1/F -- our metric inverted |
| Central field per watt | B_center / P | Ignores uniformity entirely |

The chosen metric F = B_avg / (sigma_B * P) is the most natural single number that captures all three concerns (field strength, uniformity, efficiency) without arbitrary thresholds.

---

## Step 3: Geometry Comparison

### Test conditions

All geometries evaluated under identical conditions:

| Parameter | Value |
|-----------|-------|
| Coil radius | 5 cm |
| Wire diameter | 0.5 mm (24 AWG copper) |
| Drive current | 1 A |
| Turns | 10 |
| Target volume | 2 cm diameter sphere at center |
| Sample points | 512 (regular 8x8x8 grid) |
| Copper resistivity | 1.68e-8 ohm*m (20C) |

### Geometries tested

1. **Helmholtz pair** -- two circular coils, separation = R (standard)
2. **Lee-Whiting four-coil** -- two inner + two outer coils, spacing and turn ratios from Lee-Whiting (1957) AECL CRT-673
3. **Maxwell three-coil** -- center coil + two outer coils at z = +/- sqrt(3)/2 * R, outer turns = 4/7 * center turns
4. **Conical pair (30 deg)** -- concentric circular loops on a conical surface, 30 degree half-angle
5. **Conical pair (45 deg)** -- same, 45 degree half-angle
6. **Elliptical pair** -- elliptical loops (a/b = 1.43), Helmholtz-style separation
7. **Racetrack pair** -- straight sections + semicircular end caps, Helmholtz-style separation
8. **Modified Helmholtz (0.9R separation)** -- slightly closer than standard
9. **Modified Helmholtz (1.1R separation)** -- slightly wider than standard

### Results

Sorted by figure of merit (best first):

| Geometry | B_avg (uT) | Non-Uniformity (%) | Power (mW) | FoM (1/W) | Wire Length (m) |
|----------|-----------|-------------------|-----------|----------|----------------|
| Helmholtz | 180.0 | 0.169 | 541.9 | 1091.7 | 6.33 |
| Lee-Whiting 4-coil | 207.4 | 0.151 | 776.1 | 851.0 | 9.07 |
| Helmholtz (0.9R sep) | 190.7 | 0.347 | 541.4 | 531.6 | 6.33 |
| Helmholtz (1.1R sep) | 169.2 | 0.431 | 542.3 | 427.7 | 6.34 |
| Conical (30 deg) | 183.5 | 0.948 | 553.0 | 190.7 | 6.46 |
| Conical (45 deg) | 197.4 | 1.054 | 517.3 | 183.3 | 6.05 |
| Elliptical (a/b=1.43) | 189.3 | 1.485 | 464.8 | 144.9 | 5.43 |
| Maxwell 3-coil | 190.7 | 1.245 | 602.5 | 133.3 | 7.04 |
| Racetrack | 117.4 | 36.000 | 444.2 | 6.3 | 5.19 |

### Interpretation

1. **Helmholtz wins on FoM.** This is the expected result -- Helmholtz is already analytically optimized for central uniformity with minimal hardware. It should be hard to beat.

2. **Lee-Whiting has better raw uniformity (0.151% vs 0.169%)** but uses 43% more wire and 43% more power, so its FoM is lower. This confirms the metric is working correctly -- it penalizes brute-force approaches.

3. **Modified Helmholtz spacing confirms sensitivity.** Moving from 1.0R to 0.9R or 1.1R separation degrades FoM by 50-60%. The standard Helmholtz spacing is a true optimum, not just a convention.

4. **Conical coils score worse than Helmholtz.** This contradicts Nieves (2019), who showed conical coils outperforming Helmholtz on uniformity alone. **However**, my conical implementation is a simplified approximation (concentric rings at varying heights), not the exact geometry from the paper. This result needs verification with a proper conical coil model before drawing conclusions.

5. **Maxwell three-coil scores poorly.** This appears to be a turn-ratio discretization issue -- the outer coils should have exactly 4/7 of center turns, but rounding to integer turns introduces error. Real Maxwell coils use precise current ratios, not integer turn counts.

6. **Racetrack is eliminated.** 36% non-uniformity makes it unsuitable for this application. This is a correct physical result -- the straight sections create strong field gradients that the end caps cannot compensate for.

### Known limitations

- **Conical coil geometry is approximate.** Needs re-implementation to match Nieves (2019) exactly.
- **Maxwell coil turn ratio is discretized.** Integer turns force rounding of the 4/7 ratio. A current-ratio approach (different currents per coil) would be more faithful.
- **Target volume is small (2 cm sphere in a 10 cm coil).** Results may change for larger target volumes relative to coil size. A volume sweep is needed.
- **No optimization yet.** These are standard geometries with standard parameters. The real question -- whether a non-standard geometry with optimized parameters can beat Helmholtz -- has not been answered.
- **Single operating point.** Results are for 1A, 10 turns, 5cm radius. Scaling behavior has not been verified (though Biot-Savart linearity suggests rankings should be scale-invariant for the same relative target volume).

---

## What would change my conclusions

- If a proper conical coil implementation (per Nieves 2019) scores FoM > 1092, it would be worth investigating further. The current naive implementation does not faithfully reproduce the Nieves geometry and cannot be used to draw conclusions about conical coils.
- If the FoM ranking is unstable across different target volume sizes, the metric needs modification. (Partially addressed in extended_analysis.py -- Lee-Whiting outperforms Helmholtz for tall volumes, as expected from its higher-order gradient cancellation.)
- If bench measurements disagree with simulation by >15%, the model has unaddressed systematic errors that must be resolved before any geometry comparison is meaningful.

---

## Next steps (pending review)

**Step 4:** Build one physical Helmholtz pair and measure with Hall sensor.
**Step 5:** Compare measured centerline field to simulation (target: <10% error).
**Step 6:** Test one modified geometry and check if measured improvement direction matches simulation.

---

## References

1. G. E. Lee-Whiting, "Uniform Magnetic Fields," Atomic Energy of Canada Ltd., Chalk River, ON, Canada, Tech. Rep. AECL-419 (CRT-673), 1957. Available: [https://www.osti.gov/biblio/4156720](https://www.osti.gov/biblio/4156720)

2. R. Merritt, C. Purcell, and G. Stroink, "Uniform magnetic field produced by three, four, and five square coils," *Rev. Sci. Instrum.*, vol. 54, no. 7, pp. 879--882, 1983. DOI: [10.1063/1.1137480](https://doi.org/10.1063/1.1137480) -- *Note: this paper covers square coil systems, not circular. Cited here for the multi-coil uniform field design methodology, not as direct validation of the circular-coil comparisons in this report.*

3. F. J. Nieves, A. Bayon, and F. Gascon, "Optimization of the magnetic field homogeneity of circular and conical coil pairs," *Rev. Sci. Instrum.*, vol. 90, no. 4, 045120, 2019. DOI: [10.1063/1.5079476](https://doi.org/10.1063/1.5079476)

4. B. Zhu, Y. Lu, Y. Yang, M. Zhang, and L. Jiang, "Multi-objective optimization design of the large-scale high-intensity homogeneous magnetic field coil system based on non-dominated sorting genetic algorithm (NSGA-II)," *IET Electr. Power Appl.*, vol. 16, no. 6, pp. 710--722, 2022. DOI: [10.1049/elp2.12188](https://doi.org/10.1049/elp2.12188)

5. Y. Lu, Y. Yang, M. Zhang, B. Zhu, and L. Jiang, "Improved square-coil configurations for homogeneous magnetic field generation," *IEEE Trans. Ind. Electron.*, vol. 69, no. 6, pp. 6350--6360, 2022. DOI: [10.1109/TIE.2021.3090702](https://doi.org/10.1109/TIE.2021.3090702) -- *Note: previously misattributed to Restrepo-Alvarez et al. in an earlier version of this report. Corrected after DOI verification.*

6. P. J. Hobson, N. L. Hardwicke, A. Davis, T. Smith, C. Morley, M. Packer, N. Holmes, M. A. Sheridan, M. Brookes, R. Bowtell, and M. Fromhold, "Designing optimal loop, saddle, and ellipse-based magnetic coils by spherical harmonic mapping," *IEEE Trans. Instrum. Meas.*, vol. 72, 1005815, pp. 1--15, 2023. DOI: [10.1109/TIM.2023.3284138](https://doi.org/10.1109/TIM.2023.3284138) -- *Note: previously misattributed to Bidinosti et al. in an earlier version of this report. Corrected after DOI verification. Also available: [arXiv:2305.00572](https://arxiv.org/abs/2305.00572)*

7. F. J. Salazar, F. J. Nieves, A. Bayon, and F. Gascon, "Magnetic field homogeneity of a conical coaxial coil pair," *Rev. Sci. Instrum.*, vol. 88, no. 9, 095107, 2017. DOI: [10.1063/1.5002572](https://doi.org/10.1063/1.5002572)

---

## Reproducibility

All code is in `coil_optimization.py`. Dependencies: Python 3.x, numpy, matplotlib. No external data. Run with `python coil_optimization.py` to reproduce all results and plots.
