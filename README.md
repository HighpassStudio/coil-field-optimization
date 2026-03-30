# Coil Field Optimization

Systematic comparison of magnetic coil geometries for **field uniformity per watt** of resistive dissipation.

## What This Is

A Biot-Savart field solver + geometry library that evaluates coil designs using a single figure of merit:

```
F = B_avg / (sigma_B * P)
```

Where B_avg is mean field, sigma_B is field variation over a target volume, and P is resistive power.

Higher F = more uniform field per watt of heating.

## Status

- [x] Biot-Savart solver validated against analytical Helmholtz (0.01% error)
- [x] Figure of merit defined and producing sensible rankings
- [x] 9 geometries compared (Helmholtz, Lee-Whiting, Maxwell, conical, elliptical, racetrack)
- [ ] Parameter optimization (genetic algorithm / grid search)
- [ ] Bench validation with Hall sensor
- [ ] Non-standard geometry deep dive

See [COIL_OPTIMIZATION_REPORT.md](COIL_OPTIMIZATION_REPORT.md) for full methodology, results, and references.

## Quick Start

```bash
pip install numpy matplotlib
python coil_optimization.py
```

Produces:
- Validation checks (analytical vs numerical)
- Geometry comparison table
- `coil_optimization_results.png` -- four-panel comparison plot

## Results Preview

| Geometry | Non-Uniformity | Power (mW) | FoM (1/W) |
|----------|---------------|-----------|----------|
| Helmholtz | 0.169% | 542 | 1092 |
| Lee-Whiting 4-coil | 0.151% | 776 | 851 |
| Helmholtz (0.9R sep) | 0.347% | 541 | 532 |
| Conical (30 deg) | 0.948% | 553 | 191 |
| Racetrack | 36.0% | 444 | 6 |

Standard Helmholtz wins on FoM. The open question: can optimized non-standard geometries beat it?

## Dependencies

- Python 3.x
- numpy
- matplotlib

No external data. All physics from first principles (Biot-Savart law).

## License

MIT
