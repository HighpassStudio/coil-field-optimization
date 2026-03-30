"""
Bench Test Predictions
======================
Generate exact predicted values for the physical Helmholtz build.

These are the numbers the bench must reproduce within 5-10%
for the model to be validated.

Coil spec: R=5cm, N=20 turns, 24 AWG magnet wire (0.511mm bare diameter)
Currents: 0.5A, 1.0A, 1.5A
Separations: 0.9R, 1.0R (standard), 1.1R
"""

import numpy as np
import sys
import os

# Import from main module
sys.path.insert(0, os.path.dirname(__file__))
from coil_optimization import (
    biot_savart, make_helmholtz_pair, make_circular_loop,
    coil_resistance, coil_power, analytical_helmholtz_on_axis,
    analytical_loop_on_axis, MU_0, RHO_COPPER,
    sample_grid, compute_figure_of_merit,
)


def main():
    # === COIL SPECIFICATIONS ===
    # Matching what you'll actually build
    radius = 0.05          # 5 cm
    n_turns = 20           # 20 turns per coil (easy to count, enough signal)
    wire_d_bare = 0.511e-3 # 24 AWG bare diameter (m)
    wire_d_insulated = 0.559e-3  # with enamel coating
    currents = [0.5, 1.0, 1.5]  # A
    separations = [0.9, 1.0, 1.1]  # multiples of R

    print("=" * 70)
    print("BENCH TEST PREDICTIONS")
    print("=" * 70)
    print(f"\nCoil radius: {radius*100:.0f} cm")
    print(f"Turns per coil: {n_turns}")
    print(f"Wire: 24 AWG magnet wire ({wire_d_bare*1000:.3f} mm bare)")
    print(f"Test currents: {currents} A")
    print(f"Test separations: {[f'{s}R = {s*radius*100:.1f} cm' for s in separations]}")

    # === COIL PHYSICAL PROPERTIES ===
    wire_length_per_turn = 2 * np.pi * radius  # m
    wire_length_total = wire_length_per_turn * n_turns * 2  # 2 coils
    wire_area = np.pi / 4 * wire_d_bare**2
    resistance = RHO_COPPER * wire_length_total / wire_area

    print(f"\n--- Coil Physical Properties ---")
    print(f"Wire length per turn: {wire_length_per_turn*100:.1f} cm")
    print(f"Wire length total (both coils): {wire_length_total:.2f} m")
    print(f"Resistance (theoretical, 20C): {resistance:.3f} ohm")
    print(f"  (measure with multimeter -- should be close)")

    # Winding thickness estimate
    turns_per_layer = int(radius * 0.3 / wire_d_insulated)  # ~30% of radius for winding width
    n_layers = int(np.ceil(n_turns / max(turns_per_layer, 1)))
    print(f"Approx winding: {turns_per_layer} turns/layer x {n_layers} layers")
    print(f"Winding width: ~{turns_per_layer * wire_d_insulated * 1000:.1f} mm")
    print(f"Winding depth: ~{n_layers * wire_d_insulated * 1000:.1f} mm")

    # === FIELD PREDICTIONS ===
    print(f"\n--- Predicted Center Field (z=0) ---")
    print(f"{'Separation':<15} {'Current':<10} {'B_center (uT)':<15} {'Power (mW)':<12}")
    print("-" * 55)

    for sep_mult in separations:
        sep = sep_mult * radius
        for I in currents:
            # Analytical prediction (exact for thin-wire approximation)
            B_center = 0.0
            B_center += analytical_loop_on_axis(radius, I * n_turns, sep / 2)
            B_center += analytical_loop_on_axis(radius, I * n_turns, -sep / 2)
            P = I**2 * resistance
            print(f"{sep_mult:.1f}R = {sep*100:.1f}cm  {I:.1f} A     "
                  f"{B_center*1e6:>10.1f}       {P*1000:>8.1f}")

    # === AXIAL PROFILE PREDICTIONS ===
    print(f"\n--- Predicted On-Axis Profile (I = 1.0 A) ---")
    print(f"These are the values to compare against Hall sensor measurements")
    print(f"along the z-axis (centerline between coils).\n")

    z_positions_cm = np.arange(-5, 5.5, 0.5)  # -5 to +5 cm in 0.5 cm steps
    z_positions_m = z_positions_cm / 100.0

    for sep_mult in separations:
        sep = sep_mult * radius
        I = 1.0
        print(f"\nSeparation = {sep_mult:.1f}R = {sep*100:.1f} cm, I = {I} A:")
        print(f"{'z (cm)':<10} {'B_z (uT)':<12} {'B/B_center':<12}")
        print("-" * 35)

        B_center = (analytical_loop_on_axis(radius, I * n_turns, sep / 2)
                    + analytical_loop_on_axis(radius, I * n_turns, -sep / 2))

        for z_cm, z_m in zip(z_positions_cm, z_positions_m):
            B_z = (analytical_loop_on_axis(radius, I * n_turns, z_m - sep / 2)
                   + analytical_loop_on_axis(radius, I * n_turns, z_m + sep / 2))
            ratio = B_z / B_center if B_center > 0 else 0
            print(f"{z_cm:>7.1f}   {B_z*1e6:>10.2f}   {ratio:>10.4f}")

    # === UNIFORMITY PREDICTIONS ===
    print(f"\n--- Predicted Uniformity Over 2cm Sphere (I = 1.0 A) ---")
    print(f"{'Separation':<15} {'B_avg (uT)':<12} {'Non-unif %':<12} "
          f"{'Power (mW)':<12} {'FoM (1/W)':<12}")
    print("-" * 65)

    target_points = sample_grid(np.array([0, 0, 0]), 0.01, n_per_axis=8)

    for sep_mult in separations:
        sep = sep_mult * radius
        I = 1.0
        normal = np.array([0, 0, 1.0])

        coil1 = make_circular_loop(radius, np.array([0, 0, sep/2]),
                                   normal, 400, n_turns)
        coil2 = make_circular_loop(radius, np.array([0, 0, -sep/2]),
                                   normal, 400, n_turns)
        coil = np.vstack([coil1, coil2])

        B = biot_savart(coil, I, target_points)
        B_mag = np.linalg.norm(B, axis=1)
        P = I**2 * resistance

        F, B_avg, sigma_B, uniformity_pct = compute_figure_of_merit(B_mag, P)

        print(f"{sep_mult:.1f}R = {sep*100:.1f}cm  {B_avg*1e6:>10.1f}   "
              f"{uniformity_pct:>10.3f}   {P*1000:>10.1f}   {F:>10.1f}")

    # === WHAT SUCCESS LOOKS LIKE ===
    print(f"\n{'=' * 70}")
    print("VALIDATION CRITERIA")
    print(f"{'=' * 70}")
    print("""
1. RESISTANCE CHECK
   Measure coil resistance with multimeter.
   Expected: {:.3f} ohm (at 20C)
   Pass: within 20% (accounts for temperature, connections)

2. CENTER FIELD LINEARITY
   Measure B at center for 0.5, 1.0, 1.5 A.
   B should scale linearly with I.
   Pass: R^2 > 0.99 on linear fit

3. CENTER FIELD MAGNITUDE
   At 1.0 A, standard Helmholtz:
   Expected: {:.1f} uT
   Pass: within 10%

4. AXIAL PROFILE SHAPE
   Measure B at z = -4, -3, -2, -1, 0, +1, +2, +3, +4 cm.
   Normalize to center value.
   Pass: all normalized values within 5% of prediction

5. SEPARATION COMPARISON (the key test)
   At standard Helmholtz (1.0R), B profile should be flatter
   than at 0.9R or 1.1R.
   Pass: measured non-uniformity ranking matches prediction:
         1.0R < 0.9R < 1.1R
""".format(resistance,
           (analytical_loop_on_axis(radius, 1.0 * n_turns, radius/2)
            + analytical_loop_on_axis(radius, 1.0 * n_turns, -radius/2)) * 1e6))


if __name__ == '__main__':
    main()
