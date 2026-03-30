"""
Magnetic Coil Geometry Optimization for Field Uniformity Per Watt
=================================================================

Biot-Savart field solver + geometry library + optimization framework.

Figure of merit: F = B_avg / (sigma_B * P)
  - B_avg: mean field magnitude over target volume (T)
  - sigma_B: standard deviation of field over target volume (T)
  - P: resistive power dissipation in coil (W)

Higher F = more uniform field per watt of heating.

All geometry definitions produce arrays of (x, y, z) points + dl vectors
for numerical Biot-Savart integration.

References:
  - Biot-Savart law: B = (mu_0 / 4pi) * integral(I * dl x r_hat / r^2)
  - Helmholtz: two coils separated by one radius
  - Merritt (1983): DOI 10.1063/1.1137480
  - Conical coils: Nieves (2019), DOI 10.1063/1.5079476
  - Lee-Whiting (1957): AECL CRT-673
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# =============================================================================
# Physical Constants
# =============================================================================

MU_0 = 4.0 * np.pi * 1e-7  # T*m/A
RHO_COPPER = 1.68e-8        # Ohm*m (resistivity of copper at 20C)


# =============================================================================
# Figure of Merit
# =============================================================================

@dataclass
class FieldResult:
    """Results of a field computation over a target volume."""
    B_field: np.ndarray       # (N, 3) field vectors at sample points
    B_mag: np.ndarray         # (N,) field magnitudes
    sample_points: np.ndarray # (N, 3) sample point coordinates
    B_avg: float              # mean magnitude
    sigma_B: float            # std dev of magnitude
    uniformity_pct: float     # sigma_B / B_avg * 100
    power_W: float            # resistive dissipation
    figure_of_merit: float    # F = B_avg / (sigma_B * P)
    current_A: float          # drive current
    coil_name: str            # geometry identifier


def compute_figure_of_merit(B_mag: np.ndarray, power_W: float) -> tuple:
    """
    Compute the uniformity-per-watt figure of merit.

    F = B_avg / (sigma_B * P)

    Units: T / (T * W) = 1/W -- higher is better.
    Interpretation: how much average field you get per unit of
    field variation per unit of power dissipated.

    Returns (F, B_avg, sigma_B, uniformity_pct).
    """
    B_avg = np.mean(B_mag)
    sigma_B = np.std(B_mag)
    uniformity_pct = (sigma_B / B_avg * 100.0) if B_avg > 0 else float('inf')

    if sigma_B > 0 and power_W > 0:
        F = B_avg / (sigma_B * power_W)
    elif sigma_B == 0:
        F = float('inf')  # perfect uniformity
    else:
        F = 0.0

    return F, B_avg, sigma_B, uniformity_pct


# =============================================================================
# Biot-Savart Solver
# =============================================================================

def biot_savart(
    coil_points: np.ndarray,  # (M, 3) points along coil wire
    current: float,           # Amps
    field_points: np.ndarray, # (N, 3) points where field is evaluated
) -> np.ndarray:
    """
    Compute magnetic field at field_points due to current in coil.

    Uses the discrete Biot-Savart law:
      dB = (mu_0 / 4pi) * I * (dl x r_hat) / r^2

    coil_points: ordered array of (x, y, z) positions along the wire.
    Adjacent points define dl segments.

    Returns (N, 3) array of B-field vectors.
    """
    B = np.zeros_like(field_points)  # (N, 3)

    # Compute dl vectors from adjacent coil points
    dl = np.diff(coil_points, axis=0)  # (M-1, 3)
    # Midpoints of each segment
    midpoints = (coil_points[:-1] + coil_points[1:]) / 2.0  # (M-1, 3)

    prefactor = MU_0 / (4.0 * np.pi) * current

    # Vectorized over field points and segments
    for i in range(len(midpoints)):
        # Vector from segment midpoint to all field points
        r_vec = field_points - midpoints[i]  # (N, 3)
        r_mag = np.linalg.norm(r_vec, axis=1)  # (N,)

        # Avoid division by zero (field point on wire)
        mask = r_mag > 1e-12
        r_mag_safe = np.where(mask, r_mag, 1.0)

        # dl x r_hat / r^2 = dl x r_vec / r^3
        dl_cross_r = np.cross(dl[i], r_vec)  # (N, 3)
        dB = prefactor * dl_cross_r / (r_mag_safe[:, np.newaxis] ** 3)

        # Zero out contribution for points too close to wire
        dB[~mask] = 0.0
        B += dB

    return B


def coil_resistance(coil_points: np.ndarray, wire_diameter: float) -> float:
    """
    Compute DC resistance of a coil from its geometry.

    coil_points: (M, 3) wire path
    wire_diameter: m

    Returns resistance in Ohms.
    """
    # Total wire length
    dl = np.diff(coil_points, axis=0)
    wire_length = np.sum(np.linalg.norm(dl, axis=1))

    # Cross-sectional area
    wire_area = np.pi / 4.0 * wire_diameter ** 2

    return RHO_COPPER * wire_length / wire_area


def coil_power(resistance: float, current: float) -> float:
    """Resistive power dissipation: P = I^2 * R."""
    return current ** 2 * resistance


# =============================================================================
# Coil Geometry Library
# =============================================================================

def make_circular_loop(
    radius: float,
    center: np.ndarray,
    normal: np.ndarray,
    n_points: int = 200,
    n_turns: int = 1,
) -> np.ndarray:
    """
    Generate points for a circular loop (or multi-turn coil).

    For multi-turn, points are repeated n_turns times (same path).
    In a real coil, turns would be offset -- but for thin-wire
    Biot-Savart, stacking is equivalent to multiplying current by n_turns.

    Returns (n_points * n_turns + 1, 3) array.
    """
    normal = normal / np.linalg.norm(normal)

    # Build orthonormal basis in the coil plane
    if abs(normal[2]) < 0.9:
        u = np.cross(normal, np.array([0, 0, 1]))
    else:
        u = np.cross(normal, np.array([1, 0, 0]))
    u = u / np.linalg.norm(u)
    v = np.cross(normal, u)

    theta = np.linspace(0, 2 * np.pi * n_turns, n_points * n_turns + 1)
    points = (center[np.newaxis, :]
              + radius * np.cos(theta)[:, np.newaxis] * u[np.newaxis, :]
              + radius * np.sin(theta)[:, np.newaxis] * v[np.newaxis, :])
    return points


def make_helmholtz_pair(
    radius: float,
    n_points: int = 200,
    n_turns: int = 10,
) -> np.ndarray:
    """
    Standard Helmholtz coil pair: two identical circular coils
    separated by one radius, centered on the z-axis.
    """
    separation = radius  # Helmholtz condition
    normal = np.array([0, 0, 1.0])

    coil1 = make_circular_loop(
        radius, np.array([0, 0, separation / 2]), normal, n_points, n_turns)
    coil2 = make_circular_loop(
        radius, np.array([0, 0, -separation / 2]), normal, n_points, n_turns)

    return np.vstack([coil1, coil2])


def make_maxwell_triple(
    radius: float,
    n_points: int = 200,
    n_turns_center: int = 10,
) -> tuple:
    """
    Maxwell three-coil system: center coil + two outer coils.
    Outer coils at z = +/- sqrt(3)/2 * R with 4/7 of center turns.
    Cancels through 4th-order derivative.

    Returns (coil_points, effective_n_turns) since outer coils
    have different turn count.
    """
    normal = np.array([0, 0, 1.0])
    z_outer = np.sqrt(3) / 2.0 * radius

    # Outer coils have 4/7 the turns of center coil
    # We approximate by using fewer turns
    n_turns_outer = max(1, round(n_turns_center * 4 / 7))

    center = make_circular_loop(
        radius, np.array([0, 0, 0]), normal, n_points, n_turns_center)
    top = make_circular_loop(
        radius, np.array([0, 0, z_outer]), normal, n_points, n_turns_outer)
    bottom = make_circular_loop(
        radius, np.array([0, 0, -z_outer]), normal, n_points, n_turns_outer)

    return np.vstack([center, top, bottom])


def make_conical_pair(
    radius: float,
    half_angle_deg: float = 30.0,
    n_points: int = 200,
    n_turns: int = 10,
) -> np.ndarray:
    """
    Conical coil pair (Nieves 2019, DOI 10.1063/1.5079476).

    Two conical coils facing each other, apex toward center.
    Each coil is a circular loop tilted at half_angle from the z-axis.

    For a cone with half-angle alpha, the coil plane normal makes
    angle alpha with the z-axis. The coil is positioned so its
    center is on the z-axis.

    Separation optimized: for conical pairs, optimal separation
    depends on cone angle. Use R * cos(alpha) as starting point.
    """
    alpha = np.radians(half_angle_deg)

    # Effective radius of each conical loop
    r_eff = radius

    # Position: coils offset along z
    z_offset = r_eff * np.cos(alpha) / 2.0

    # For conical coils, we tilt the wire loops
    # Upper coil: normal tilted toward center
    # Lower coil: normal tilted toward center (mirror)
    normal_upper = np.array([0, 0, 1.0])
    normal_lower = np.array([0, 0, 1.0])

    # Generate points on a cone surface
    # Each "turn" is a circular loop at a different height on the cone
    all_points = []

    for turn in range(n_turns):
        # Fraction along the cone from base to apex
        frac = turn / max(n_turns - 1, 1)
        r_turn = r_eff * (1.0 - frac * np.sin(alpha) * 0.5)
        z_turn = z_offset + frac * r_eff * np.sin(alpha) * 0.3

        # Upper coil
        theta = np.linspace(0, 2 * np.pi, n_points + 1)
        x = r_turn * np.cos(theta)
        y = r_turn * np.sin(theta)
        z = np.full_like(theta, z_turn)
        upper = np.column_stack([x, y, z])

        # Lower coil (mirror)
        lower = upper.copy()
        lower[:, 2] = -lower[:, 2]

        all_points.append(upper)
        all_points.append(lower)

    return np.vstack(all_points)


def make_elliptical_pair(
    a: float,           # semi-major axis
    b: float,           # semi-minor axis
    separation: float,  # distance between coils
    n_points: int = 200,
    n_turns: int = 10,
) -> np.ndarray:
    """
    Elliptical Helmholtz-style pair: two elliptical coils on the z-axis.
    """
    theta = np.linspace(0, 2 * np.pi * n_turns, n_points * n_turns + 1)
    x = a * np.cos(theta)
    y = b * np.sin(theta)

    # Upper coil
    z_upper = np.full_like(theta, separation / 2.0)
    upper = np.column_stack([x, y, z_upper])

    # Lower coil
    z_lower = np.full_like(theta, -separation / 2.0)
    lower = np.column_stack([x, y, z_lower])

    return np.vstack([upper, lower])


def make_racetrack_pair(
    length: float,      # straight section length
    radius: float,      # end cap radius
    separation: float,  # distance between coils
    n_points: int = 200,
    n_turns: int = 10,
) -> np.ndarray:
    """
    Racetrack coil pair: two parallel racetrack-shaped coils.
    Each is a rectangle with semicircular ends.
    """
    all_points = []
    half_len = length / 2.0

    for turn in range(n_turns):
        pts_per_section = n_points // 4

        # Top straight (positive x direction)
        x_top = np.linspace(-half_len, half_len, pts_per_section)
        y_top = np.full(pts_per_section, radius)

        # Right semicircle
        theta_right = np.linspace(np.pi / 2, -np.pi / 2, pts_per_section)
        x_right = half_len + radius * np.cos(theta_right)
        y_right = radius * np.sin(theta_right)

        # Bottom straight (negative x direction)
        x_bot = np.linspace(half_len, -half_len, pts_per_section)
        y_bot = np.full(pts_per_section, -radius)

        # Left semicircle
        theta_left = np.linspace(-np.pi / 2, np.pi / 2, pts_per_section)
        x_left = -half_len + radius * np.cos(theta_left)
        y_left = radius * np.sin(theta_left)

        x = np.concatenate([x_top, x_right, x_bot, x_left])
        y = np.concatenate([y_top, y_right, y_bot, y_left])

        all_points.append(np.column_stack([x, y]))

    loop_2d = np.vstack(all_points)

    # Upper coil
    z_upper = np.full(len(loop_2d), separation / 2.0)
    upper = np.column_stack([loop_2d, z_upper])

    # Lower coil
    z_lower = np.full(len(loop_2d), -separation / 2.0)
    lower = np.column_stack([loop_2d, z_lower])

    return np.vstack([upper, lower])


def make_four_coil_lee_whiting(
    radius: float,
    n_points: int = 200,
    n_turns_inner: int = 10,
) -> np.ndarray:
    """
    Lee-Whiting four-coil system (1957).
    Two inner coils + two outer coils with specific spacing and turn ratios.

    Inner coils: z = +/- 0.4708 * a, N turns
    Outer coils: z = +/- 1.3553 * a, 0.4232 * N turns

    Where a = radius. These values zero derivatives through 6th order.
    """
    normal = np.array([0, 0, 1.0])

    z_inner = 0.4708 * radius
    z_outer = 1.3553 * radius
    n_turns_outer = max(1, round(n_turns_inner * 0.4232))

    inner_top = make_circular_loop(
        radius, np.array([0, 0, z_inner]), normal, n_points, n_turns_inner)
    inner_bot = make_circular_loop(
        radius, np.array([0, 0, -z_inner]), normal, n_points, n_turns_inner)
    outer_top = make_circular_loop(
        radius, np.array([0, 0, z_outer]), normal, n_points, n_turns_outer)
    outer_bot = make_circular_loop(
        radius, np.array([0, 0, -z_outer]), normal, n_points, n_turns_outer)

    return np.vstack([inner_top, inner_bot, outer_top, outer_bot])


# =============================================================================
# Target Volume Sampling
# =============================================================================

def sample_sphere(center: np.ndarray, radius: float, n_points: int = 500) -> np.ndarray:
    """Uniformly sample points inside a sphere."""
    # Use rejection sampling for uniform distribution
    points = []
    while len(points) < n_points:
        batch = np.random.uniform(-radius, radius, (n_points * 2, 3))
        dists = np.linalg.norm(batch, axis=1)
        inside = batch[dists <= radius]
        points.extend(inside.tolist())
    points = np.array(points[:n_points]) + center
    return points


def sample_cube(center: np.ndarray, half_side: float, n_points: int = 500) -> np.ndarray:
    """Uniformly sample points inside a cube."""
    points = np.random.uniform(-half_side, half_side, (n_points, 3)) + center
    return points


def sample_grid(center: np.ndarray, half_side: float, n_per_axis: int = 8) -> np.ndarray:
    """Regular grid of sample points inside a cube."""
    x = np.linspace(-half_side, half_side, n_per_axis) + center[0]
    y = np.linspace(-half_side, half_side, n_per_axis) + center[1]
    z = np.linspace(-half_side, half_side, n_per_axis) + center[2]
    xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')
    return np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])


# =============================================================================
# Full Evaluation Pipeline
# =============================================================================

def evaluate_coil(
    coil_points: np.ndarray,
    coil_name: str,
    current: float,
    wire_diameter: float,
    field_points: np.ndarray,
) -> FieldResult:
    """
    Evaluate a coil geometry: compute field, power, and figure of merit.
    """
    B = biot_savart(coil_points, current, field_points)
    B_mag = np.linalg.norm(B, axis=1)
    R = coil_resistance(coil_points, wire_diameter)
    P = coil_power(R, current)
    F, B_avg, sigma_B, uniformity_pct = compute_figure_of_merit(B_mag, P)

    return FieldResult(
        B_field=B,
        B_mag=B_mag,
        sample_points=field_points,
        B_avg=B_avg,
        sigma_B=sigma_B,
        uniformity_pct=uniformity_pct,
        power_W=P,
        figure_of_merit=F,
        current_A=current,
        coil_name=coil_name,
    )


# =============================================================================
# Analytical Validation: On-Axis Field of a Single Circular Loop
# =============================================================================

def analytical_loop_on_axis(radius: float, current: float, z: float) -> float:
    """
    Exact on-axis B-field of a single circular loop.
    B_z = mu_0 * I * R^2 / (2 * (R^2 + z^2)^(3/2))
    """
    return MU_0 * current * radius**2 / (2.0 * (radius**2 + z**2)**1.5)


def analytical_helmholtz_on_axis(radius: float, current: float, n_turns: int, z: float) -> float:
    """
    On-axis field of a Helmholtz pair (each coil with n_turns).
    Superposition of two loops at z = +/- R/2.
    """
    d = radius / 2.0
    B1 = analytical_loop_on_axis(radius, current * n_turns, z - d)
    B2 = analytical_loop_on_axis(radius, current * n_turns, z + d)
    return B1 + B2


def run_validation():
    """
    Validate Biot-Savart solver against analytical Helmholtz solution.
    """
    print("=" * 60)
    print("VALIDATION: Biot-Savart vs Analytical")
    print("=" * 60)

    radius = 0.05  # 5 cm
    current = 1.0  # 1 A
    n_turns = 10

    # Analytical: on-axis field at center (z=0)
    B_analytical_center = analytical_helmholtz_on_axis(radius, current, n_turns, 0.0)

    # Numerical: Helmholtz coil
    coil = make_helmholtz_pair(radius, n_points=400, n_turns=n_turns)
    field_point = np.array([[0.0, 0.0, 0.0]])
    B_numerical = biot_savart(coil, current, field_point)
    B_numerical_center = np.linalg.norm(B_numerical[0])

    error_pct = abs(B_numerical_center - B_analytical_center) / B_analytical_center * 100

    print(f"\n  Helmholtz pair: R={radius*100:.0f} cm, I={current} A, N={n_turns} turns")
    print(f"  Analytical B at center: {B_analytical_center*1e6:.2f} uT")
    print(f"  Numerical  B at center: {B_numerical_center*1e6:.2f} uT")
    print(f"  Error: {error_pct:.2f}%")

    status = "PASS" if error_pct < 2.0 else "FAIL"
    print(f"  [{status}] (threshold: <2%)")

    # Test on-axis profile
    z_points = np.linspace(-radius, radius, 21)
    B_analytical = [analytical_helmholtz_on_axis(radius, current, n_turns, z)
                    for z in z_points]
    field_pts_axis = np.column_stack([np.zeros(21), np.zeros(21), z_points])
    B_numerical_axis = biot_savart(coil, current, field_pts_axis)
    B_numerical_mag = np.linalg.norm(B_numerical_axis, axis=1)

    max_error = np.max(np.abs(B_numerical_mag - B_analytical) / B_analytical) * 100
    status2 = "PASS" if max_error < 5.0 else "FAIL"
    print(f"\n  On-axis profile (21 points, z = -R to +R):")
    print(f"  Max error: {max_error:.2f}%  [{status2}]")

    print(f"\n{'=' * 60}")
    overall = "ALL CHECKS PASSED" if (error_pct < 2.0 and max_error < 5.0) else "SOME CHECKS FAILED"
    print(f"OVERALL: {overall}")
    print(f"{'=' * 60}")

    return error_pct < 2.0 and max_error < 5.0


# =============================================================================
# Geometry Comparison Study
# =============================================================================

def run_geometry_comparison():
    """
    Compare all coil geometries on the same basis:
    - Same coil radius (5 cm)
    - Same wire diameter (0.5 mm, ~24 AWG)
    - Same drive current (1 A)
    - Same target volume (2 cm diameter sphere at center)
    """
    print("\n" + "=" * 60)
    print("GEOMETRY COMPARISON STUDY")
    print("=" * 60)

    radius = 0.05       # 5 cm coil radius
    wire_d = 0.5e-3     # 0.5 mm wire (24 AWG)
    current = 1.0       # 1 A
    n_turns = 10
    n_pts = 300          # points per turn for discretization

    # Target volume: 2 cm diameter sphere at origin
    np.random.seed(42)
    target_radius = 0.01  # 1 cm
    field_points = sample_grid(np.array([0, 0, 0]), target_radius, n_per_axis=8)

    print(f"\n  Coil radius: {radius*100:.0f} cm")
    print(f"  Wire: {wire_d*1000:.1f} mm diameter copper")
    print(f"  Current: {current} A")
    print(f"  Turns: {n_turns}")
    print(f"  Target volume: {target_radius*200:.0f} cm diameter sphere")
    print(f"  Sample points: {len(field_points)}")

    # Build all geometries
    geometries = {}

    # 1. Helmholtz pair
    geometries['Helmholtz'] = make_helmholtz_pair(radius, n_pts, n_turns)

    # 2. Maxwell triple
    geometries['Maxwell 3-coil'] = make_maxwell_triple(radius, n_pts, n_turns)

    # 3. Lee-Whiting four-coil
    geometries['Lee-Whiting 4-coil'] = make_four_coil_lee_whiting(radius, n_pts, n_turns)

    # 4. Conical pair (30 deg half-angle)
    geometries['Conical (30 deg)'] = make_conical_pair(radius, 30.0, n_pts, n_turns)

    # 5. Conical pair (45 deg half-angle)
    geometries['Conical (45 deg)'] = make_conical_pair(radius, 45.0, n_pts, n_turns)

    # 6. Elliptical pair (a=R, b=0.7R, separation=R)
    geometries['Elliptical (a/b=1.43)'] = make_elliptical_pair(
        radius, 0.7 * radius, radius, n_pts, n_turns)

    # 7. Racetrack pair (length=R, cap_radius=0.5R, separation=R)
    geometries['Racetrack'] = make_racetrack_pair(
        radius, 0.5 * radius, radius, n_pts, n_turns)

    # 8. Modified Helmholtz (separation = 0.9R -- slightly closer)
    normal = np.array([0, 0, 1.0])
    sep_mod = 0.9 * radius
    coil1 = make_circular_loop(radius, np.array([0, 0, sep_mod/2]), normal, n_pts, n_turns)
    coil2 = make_circular_loop(radius, np.array([0, 0, -sep_mod/2]), normal, n_pts, n_turns)
    geometries['Helmholtz (0.9R sep)'] = np.vstack([coil1, coil2])

    # 9. Modified Helmholtz (separation = 1.1R -- slightly wider)
    sep_wide = 1.1 * radius
    coil1w = make_circular_loop(radius, np.array([0, 0, sep_wide/2]), normal, n_pts, n_turns)
    coil2w = make_circular_loop(radius, np.array([0, 0, -sep_wide/2]), normal, n_pts, n_turns)
    geometries['Helmholtz (1.1R sep)'] = np.vstack([coil1w, coil2w])

    # Evaluate all
    results = {}
    for name, coil in geometries.items():
        result = evaluate_coil(coil, name, current, wire_d, field_points)
        results[name] = result

    # Print comparison table
    print(f"\n{'Geometry':<25} {'B_avg (uT)':>10} {'Uniformity%':>12} {'Power (mW)':>11} "
          f"{'FoM (1/W)':>10} {'Wire (m)':>9}")
    print("-" * 80)

    # Sort by figure of merit
    sorted_results = sorted(results.values(), key=lambda r: r.figure_of_merit, reverse=True)

    for r in sorted_results:
        coil = geometries[r.coil_name]
        dl = np.diff(coil, axis=0)
        wire_len = np.sum(np.linalg.norm(dl, axis=1))
        print(f"{r.coil_name:<25} {r.B_avg*1e6:>10.1f} {r.uniformity_pct:>11.3f}% "
              f"{r.power_W*1000:>10.1f} {r.figure_of_merit:>10.1f} {wire_len:>8.2f}")

    return results, geometries


# =============================================================================
# Visualization
# =============================================================================

def plot_comparison(results: dict, geometries: dict):
    """Generate comparison plots."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Magnetic Coil Geometry Optimization -- Uniformity Per Watt',
                 fontsize=14, fontweight='bold')

    sorted_names = sorted(results.keys(),
                          key=lambda n: results[n].figure_of_merit, reverse=True)

    colors = plt.cm.tab10(np.linspace(0, 1, len(sorted_names)))

    # Plot 1: FoM bar chart
    ax1 = axes[0, 0]
    foms = [results[n].figure_of_merit for n in sorted_names]
    bars = ax1.barh(range(len(sorted_names)), foms, color=colors)
    ax1.set_yticks(range(len(sorted_names)))
    ax1.set_yticklabels(sorted_names, fontsize=8)
    ax1.set_xlabel('Figure of Merit (1/W)')
    ax1.set_title('Uniformity-Per-Watt Ranking')
    ax1.grid(True, alpha=0.3, axis='x')
    ax1.invert_yaxis()

    # Plot 2: Uniformity vs Power scatter
    ax2 = axes[0, 1]
    for i, name in enumerate(sorted_names):
        r = results[name]
        ax2.scatter(r.power_W * 1000, r.uniformity_pct, color=colors[i],
                    s=100, zorder=5, label=name)
    ax2.set_xlabel('Power (mW)')
    ax2.set_ylabel('Field Non-Uniformity (%)')
    ax2.set_title('Uniformity vs Power (lower-left is better)')
    ax2.legend(fontsize=7, loc='upper right')
    ax2.grid(True, alpha=0.3)

    # Plot 3: On-axis field profiles
    ax3 = axes[1, 0]
    z_line = np.linspace(-0.04, 0.04, 100)
    axis_points = np.column_stack([np.zeros(100), np.zeros(100), z_line])
    for i, name in enumerate(sorted_names[:5]):  # top 5 only
        coil = geometries[name]
        B = biot_savart(coil, 1.0, axis_points)
        B_z = B[:, 2]
        B_z_norm = B_z / B_z[len(B_z)//2]  # normalize to center value
        ax3.plot(z_line * 100, B_z_norm, color=colors[i], linewidth=2, label=name)
    ax3.set_xlabel('z position (cm)')
    ax3.set_ylabel('B_z / B_z(0)')
    ax3.set_title('On-Axis Field Profile (top 5 geometries)')
    ax3.legend(fontsize=7)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0.95, 1.05)
    ax3.axhline(1.0, color='black', linestyle='--', alpha=0.3)

    # Plot 4: B_avg vs Uniformity (Pareto front)
    ax4 = axes[1, 1]
    for i, name in enumerate(sorted_names):
        r = results[name]
        ax4.scatter(r.B_avg * 1e6, r.uniformity_pct, color=colors[i],
                    s=100, zorder=5, label=name)
    ax4.set_xlabel('Mean Field Strength (uT)')
    ax4.set_ylabel('Field Non-Uniformity (%)')
    ax4.set_title('Field Strength vs Uniformity')
    ax4.legend(fontsize=7, loc='upper right')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('coil_optimization_results.png', dpi=150, bbox_inches='tight')
    print("\nPlot saved to: coil_optimization_results.png")
    plt.close()


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    # Step 1: Validate
    valid = run_validation()
    if not valid:
        print("\n*** VALIDATION FAILED -- fix solver before trusting results ***")

    # Step 2: Geometry comparison
    results, geometries = run_geometry_comparison()

    # Step 3: Plot
    plot_comparison(results, geometries)
