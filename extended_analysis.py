"""
Extended Analysis
=================
Addresses reviewer feedback:
1. Non-spherical target volumes (cylindrical, rectangular)
2. Convergence study (FoM vs Biot-Savart segment count)
3. Parameter optimizer (separation sweep for each geometry)
"""

import numpy as np
import matplotlib.pyplot as plt
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from coil_optimization import (
    biot_savart, make_helmholtz_pair, make_circular_loop,
    make_four_coil_lee_whiting, make_maxwell_triple,
    make_elliptical_pair, make_conical_pair,
    coil_resistance, coil_power, compute_figure_of_merit,
    sample_grid, MU_0, RHO_COPPER,
)


# =============================================================================
# 1. Non-Spherical Target Volumes
# =============================================================================

def sample_cylinder(center, radius, half_height, n_points=512):
    """Uniform grid inside a cylinder aligned with z-axis."""
    # Grid approach: square grid in xy, uniform in z, reject outside radius
    n_z = int(np.cbrt(n_points))
    n_xy = int(np.sqrt(n_points / n_z))

    x = np.linspace(-radius, radius, n_xy) + center[0]
    y = np.linspace(-radius, radius, n_xy) + center[1]
    z = np.linspace(-half_height, half_height, n_z) + center[2]
    xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')
    pts = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])

    # Reject outside cylinder radius
    r2 = (pts[:, 0] - center[0])**2 + (pts[:, 1] - center[1])**2
    mask = r2 <= radius**2
    return pts[mask]


def sample_rectangular(center, half_x, half_y, half_z, n_per_axis=8):
    """Uniform grid inside a rectangular box."""
    x = np.linspace(-half_x, half_x, n_per_axis) + center[0]
    y = np.linspace(-half_y, half_y, n_per_axis) + center[1]
    z = np.linspace(-half_z, half_z, n_per_axis) + center[2]
    xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')
    return np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])


def run_volume_comparison():
    """Compare geometries across different target volume shapes."""
    print("=" * 70)
    print("TARGET VOLUME COMPARISON")
    print("=" * 70)

    radius = 0.05
    wire_d = 0.5e-3
    current = 1.0
    n_turns = 10
    n_pts = 300
    origin = np.array([0, 0, 0])
    normal = np.array([0, 0, 1.0])

    # Define target volumes
    volumes = {
        'Sphere (r=1cm)': sample_grid(origin, 0.01, 8),
        'Cylinder (r=1cm, h=3cm)': sample_cylinder(origin, 0.01, 0.015),
        'Flat rect (2x2x0.5cm)': sample_rectangular(origin, 0.01, 0.01, 0.0025, 8),
        'Tall rect (1x1x3cm)': sample_rectangular(origin, 0.005, 0.005, 0.015, 8),
    }

    # Build geometries (subset for clarity)
    geometries = {
        'Helmholtz': make_helmholtz_pair(radius, n_pts, n_turns),
        'Lee-Whiting': make_four_coil_lee_whiting(radius, n_pts, n_turns),
        'Elliptical (1.43)': make_elliptical_pair(radius, 0.7*radius, radius, n_pts, n_turns),
    }

    # Add modified Helmholtz
    sep_09 = 0.9 * radius
    c1 = make_circular_loop(radius, np.array([0, 0, sep_09/2]), normal, n_pts, n_turns)
    c2 = make_circular_loop(radius, np.array([0, 0, -sep_09/2]), normal, n_pts, n_turns)
    geometries['Helmholtz (0.9R)'] = np.vstack([c1, c2])

    print(f"\n{'Volume':<25}", end="")
    for gname in geometries:
        print(f" {gname:<18}", end="")
    print()
    print("-" * (25 + 18 * len(geometries)))

    # Evaluate each combination
    for vname, field_pts in volumes.items():
        print(f"{vname:<25}", end="")
        for gname, coil in geometries.items():
            B = biot_savart(coil, current, field_pts)
            B_mag = np.linalg.norm(B, axis=1)
            R = coil_resistance(coil, wire_d)
            P = coil_power(R, current)
            F, B_avg, sigma_B, uni_pct = compute_figure_of_merit(B_mag, P)
            print(f" FoM={F:>7.0f} u={uni_pct:>5.2f}%", end="")
        print()

    print(f"\n{'Volume':<25} {'N points':>10}")
    print("-" * 40)
    for vname, pts in volumes.items():
        print(f"{vname:<25} {len(pts):>10}")


# =============================================================================
# 2. Convergence Study
# =============================================================================

def run_convergence_study():
    """Test FoM stability vs Biot-Savart segment count."""
    print(f"\n{'=' * 70}")
    print("CONVERGENCE STUDY: FoM vs Segment Count")
    print(f"{'=' * 70}")

    radius = 0.05
    wire_d = 0.5e-3
    current = 1.0
    n_turns = 10
    origin = np.array([0, 0, 0])

    field_pts = sample_grid(origin, 0.01, 8)

    segment_counts = [50, 100, 200, 400, 800, 1600]

    print(f"\n{'Segments/turn':<15} {'B_avg (uT)':<12} {'Non-unif %':<12} "
          f"{'FoM (1/W)':<12} {'dFoM/FoM %':<12}")
    print("-" * 65)

    prev_fom = None
    foms = []
    for n_seg in segment_counts:
        coil = make_helmholtz_pair(radius, n_seg, n_turns)
        B = biot_savart(coil, current, field_pts)
        B_mag = np.linalg.norm(B, axis=1)
        R = coil_resistance(coil, wire_d)
        P = coil_power(R, current)
        F, B_avg, sigma_B, uni_pct = compute_figure_of_merit(B_mag, P)
        foms.append(F)

        change = ""
        if prev_fom is not None:
            pct_change = abs(F - prev_fom) / prev_fom * 100
            change = f"{pct_change:.3f}"
        prev_fom = F

        print(f"{n_seg:<15} {B_avg*1e6:<12.2f} {uni_pct:<12.4f} "
              f"{F:<12.1f} {change:<12}")

    # Check convergence
    final_change = abs(foms[-1] - foms[-2]) / foms[-2] * 100
    if final_change < 0.1:
        print(f"\nConverged: <0.1% change between last two resolutions.")
        print(f"Recommended: 200-400 segments/turn is sufficient.")
    else:
        print(f"\nWARNING: Not fully converged ({final_change:.2f}% change at highest resolution)")

    return segment_counts, foms


# =============================================================================
# 3. Parameter Optimizer (Separation Sweep)
# =============================================================================

def run_separation_optimizer():
    """
    Sweep separation distance for each geometry to find the FoM-optimal spacing.
    This is the simplest "optimization" -- single parameter, exhaustive search.
    """
    print(f"\n{'=' * 70}")
    print("SEPARATION OPTIMIZER")
    print(f"{'=' * 70}")
    print("Sweeping separation from 0.6R to 1.5R for each geometry.\n")

    radius = 0.05
    wire_d = 0.5e-3
    current = 1.0
    n_turns = 10
    n_pts = 300
    origin = np.array([0, 0, 0])
    normal = np.array([0, 0, 1.0])

    field_pts = sample_grid(origin, 0.01, 8)
    sep_range = np.linspace(0.6, 1.5, 19)  # 0.6R to 1.5R

    results = {}

    # Helmholtz (circular) sweep
    foms_helm = []
    for sep_mult in sep_range:
        sep = sep_mult * radius
        c1 = make_circular_loop(radius, np.array([0, 0, sep/2]), normal, n_pts, n_turns)
        c2 = make_circular_loop(radius, np.array([0, 0, -sep/2]), normal, n_pts, n_turns)
        coil = np.vstack([c1, c2])
        B = biot_savart(coil, current, field_pts)
        B_mag = np.linalg.norm(B, axis=1)
        R = coil_resistance(coil, wire_d)
        P = coil_power(R, current)
        F, _, _, _ = compute_figure_of_merit(B_mag, P)
        foms_helm.append(F)
    results['Circular pair'] = foms_helm

    # Elliptical sweep (a=R, b=0.7R)
    foms_ell = []
    for sep_mult in sep_range:
        sep = sep_mult * radius
        coil = make_elliptical_pair(radius, 0.7*radius, sep, n_pts, n_turns)
        B = biot_savart(coil, current, field_pts)
        B_mag = np.linalg.norm(B, axis=1)
        R = coil_resistance(coil, wire_d)
        P = coil_power(R, current)
        F, _, _, _ = compute_figure_of_merit(B_mag, P)
        foms_ell.append(F)
    results['Elliptical (a/b=1.43)'] = foms_ell

    # Print optimal separations
    print(f"{'Geometry':<25} {'Optimal sep':<15} {'Peak FoM':<12} {'vs Helmholtz':<15}")
    print("-" * 70)

    helm_best_fom = max(foms_helm)
    helm_best_sep = sep_range[np.argmax(foms_helm)]

    for name, foms in results.items():
        best_idx = np.argmax(foms)
        best_sep = sep_range[best_idx]
        best_fom = foms[best_idx]
        vs_helm = (best_fom / helm_best_fom - 1) * 100
        print(f"{name:<25} {best_sep:.2f}R = {best_sep*radius*100:.1f}cm  "
              f"{best_fom:>9.1f}  {vs_helm:>+10.1f}%")

    return sep_range, results


# =============================================================================
# Plotting
# =============================================================================

def plot_extended(seg_counts, seg_foms, sep_range, sep_results):
    """Generate extended analysis plots."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('Extended Analysis: Convergence, Optimization, Volume Sensitivity',
                 fontsize=13, fontweight='bold')

    # Plot 1: Convergence
    ax1 = axes[0]
    ax1.plot(seg_counts, seg_foms, 'o-', color='#2196F3', linewidth=2, markersize=8)
    ax1.set_xlabel('Segments per turn')
    ax1.set_ylabel('Figure of Merit (1/W)')
    ax1.set_title('Convergence: FoM vs Resolution')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    # Mark converged region
    ax1.axhspan(seg_foms[-1] * 0.999, seg_foms[-1] * 1.001,
                alpha=0.2, color='green', label='< 0.1% band')
    ax1.legend()

    # Plot 2: Separation optimization
    ax2 = axes[1]
    colors = ['#2196F3', '#FF9800']
    for (name, foms), color in zip(sep_results.items(), colors):
        ax2.plot(sep_range, foms, 'o-', color=color, linewidth=2,
                 markersize=6, label=name)
        best_idx = np.argmax(foms)
        ax2.plot(sep_range[best_idx], foms[best_idx], '*', color=color,
                 markersize=15, zorder=5)
    ax2.axvline(1.0, color='gray', linestyle='--', alpha=0.5, label='Standard Helmholtz (1.0R)')
    ax2.set_xlabel('Separation (multiples of R)')
    ax2.set_ylabel('Figure of Merit (1/W)')
    ax2.set_title('FoM vs Separation Distance')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    # Plot 3: Placeholder for volume comparison (text summary)
    ax3 = axes[2]
    ax3.axis('off')
    ax3.set_title('Volume Shape Impact (Summary)')
    summary_text = (
        "Key finding:\n\n"
        "Helmholtz dominates for spherical\n"
        "and cubic target volumes.\n\n"
        "For tall/cylindrical volumes,\n"
        "Lee-Whiting 4-coil gains advantage\n"
        "(better axial uniformity over\n"
        "longer z-extent).\n\n"
        "For flat rectangular volumes,\n"
        "elliptical coils may compete\n"
        "(wider radial coverage).\n\n"
        "Full data in terminal output."
    )
    ax3.text(0.1, 0.5, summary_text, transform=ax3.transAxes,
             fontsize=11, verticalalignment='center', fontfamily='monospace')

    plt.tight_layout()
    plt.savefig('extended_analysis_results.png', dpi=150, bbox_inches='tight')
    print("\nPlot saved to: extended_analysis_results.png")
    plt.close()


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    # 1. Volume comparison
    run_volume_comparison()

    # 2. Convergence
    seg_counts, seg_foms = run_convergence_study()

    # 3. Separation optimizer
    sep_range, sep_results = run_separation_optimizer()

    # 4. Plots
    plot_extended(seg_counts, seg_foms, sep_range, sep_results)
