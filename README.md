# Coil Field Optimization

Open-source tool for comparing magnetic coil geometries under power constraints. Uses a Biot-Savart solver with a practical engineering figure of merit (field uniformity per watt).

This is an early-stage hobby/educational project, not a novel contribution to electromagnetics theory. The underlying physics (Biot-Savart, Helmholtz optimization, multi-coil cancellation) is well-established in textbooks and published literature going back to Lee-Whiting (1957) and Merritt (1983). The goal here is to build an accessible, reproducible tool and validate it against physical hardware.

## What This Is

A numpy-based Biot-Savart field solver + geometry library that evaluates coil designs using a composite figure of merit:

```
F = B_avg / (sigma_B * P)
```

Where B_avg is mean field strength over a target volume, sigma_B is field variation, and P is resistive power dissipation. Higher F = more uniform field per watt of heating. This metric is a practical engineering heuristic, not a replacement for application-specific optimization.

## Status

- [x] Biot-Savart solver validated against analytical Helmholtz (0.01% error)
- [x] Figure of merit defined and producing sensible rankings
- [x] 9 geometries compared (Helmholtz, Lee-Whiting, Maxwell, conical, elliptical, racetrack)
- [x] Convergence study (FoM stable at 200+ segments/turn)
- [x] Separation optimizer (confirms 1.0R optimal for circular pairs)
- [x] Target volume comparison (spherical, cylindrical, rectangular)
- [ ] **Bench validation with Hall sensor (next step -- this is the gating item)**
- [ ] Fix conical coil geometry (current implementation is naive)

See [COIL_OPTIMIZATION_REPORT.md](COIL_OPTIMIZATION_REPORT.md) for full methodology, results, and references.
See [BENCH_TEST_PLAN.md](BENCH_TEST_PLAN.md) for the physical validation plan.

## Quick Start

```bash
pip install numpy matplotlib
python coil_optimization.py        # solver validation + geometry comparison
python extended_analysis.py        # convergence, volume study, separation sweep
python bench_predictions.py        # predicted values for physical build
```

## Results Summary

Standard Helmholtz wins on FoM for compact spherical target volumes. This is the expected result -- Helmholtz is analytically optimized for exactly this case.

| Geometry | Non-Uniformity | Power (mW) | FoM (1/W) |
|----------|---------------|-----------|----------|
| Helmholtz | 0.169% | 542 | 1092 |
| Lee-Whiting 4-coil | 0.151% | 776 | 851 |
| Helmholtz (0.9R sep) | 0.347% | 541 | 532 |
| Conical (30 deg)* | 0.948% | 553 | 191 |

*Conical implementation is a naive approximation (stacked rings, not proper helical conical surface per Nieves 2019). These results are not trustworthy and should not be compared against published conical coil data.

For non-spherical target volumes, Lee-Whiting outperforms Helmholtz on tall/cylindrical regions -- an expected result given its higher-order gradient cancellation along the axis.

## Known Limitations

- No physical validation yet (simulation only)
- Conical coil geometry does not match Nieves et al. (2019)
- Maxwell 3-coil uses integer turn approximation of the 4/7 current ratio
- Target volumes tested are small relative to coil size
- DC resistance only (no skin effect, no thermal limits)
- No off-axis validation beyond the central target volume
- No comparison against FEM tools (COMSOL, etc.)

## Dependencies

- Python 3.x
- numpy
- matplotlib

No external data. All physics from first principles (Biot-Savart law).

## License

MIT
