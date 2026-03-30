"""
Generate STL files for Helmholtz coil bench test hardware.

Parts:
  1. Coil form (x2) -- spool for winding 20 turns of 24 AWG at R=5cm
  2. Sensor rail -- linear slide with 0.5cm position marks and sensor holder
  3. Separation spacers -- snap-on spacers for 4.5cm, 5.0cm, 5.5cm coil spacing

All dimensions in mm. Designed for Bambu Lab A1/P1/X1 (256x256x256mm bed).
"""

import numpy as np
from stl import mesh


def cylinder_mesh(r_outer, r_inner, height, n_segments=64, z_offset=0.0):
    """
    Create a hollow cylinder (tube/ring) as triangle mesh.
    Returns list of triangle vertices [(v0, v1, v2), ...].
    """
    triangles = []
    angles = np.linspace(0, 2 * np.pi, n_segments + 1)

    for i in range(n_segments):
        a0, a1 = angles[i], angles[i + 1]
        cos0, sin0 = np.cos(a0), np.sin(a0)
        cos1, sin1 = np.cos(a1), np.sin(a1)

        z_lo = z_offset
        z_hi = z_offset + height

        # Outer surface (2 triangles per segment)
        p0 = [r_outer * cos0, r_outer * sin0, z_lo]
        p1 = [r_outer * cos1, r_outer * sin1, z_lo]
        p2 = [r_outer * cos1, r_outer * sin1, z_hi]
        p3 = [r_outer * cos0, r_outer * sin0, z_hi]
        triangles.append((p0, p1, p2))
        triangles.append((p0, p2, p3))

        # Inner surface (2 triangles, reversed normals)
        p4 = [r_inner * cos0, r_inner * sin0, z_lo]
        p5 = [r_inner * cos1, r_inner * sin1, z_lo]
        p6 = [r_inner * cos1, r_inner * sin1, z_hi]
        p7 = [r_inner * cos0, r_inner * sin0, z_hi]
        triangles.append((p5, p4, p7))
        triangles.append((p5, p7, p6))

        # Top face (annular ring)
        triangles.append((p3, p2, p6))
        triangles.append((p3, p6, p7))

        # Bottom face (annular ring)
        triangles.append((p0, p5, p1))
        triangles.append((p0, p4, p5))

    return triangles


def solid_cylinder_mesh(radius, height, n_segments=64, z_offset=0.0,
                        x_offset=0.0, y_offset=0.0):
    """Create a solid cylinder as triangle mesh."""
    triangles = []
    angles = np.linspace(0, 2 * np.pi, n_segments + 1)

    z_lo = z_offset
    z_hi = z_offset + height
    cx, cy = x_offset, y_offset

    for i in range(n_segments):
        a0, a1 = angles[i], angles[i + 1]
        cos0, sin0 = np.cos(a0), np.sin(a0)
        cos1, sin1 = np.cos(a1), np.sin(a1)

        p0 = [cx + radius * cos0, cy + radius * sin0, z_lo]
        p1 = [cx + radius * cos1, cy + radius * sin1, z_lo]
        p2 = [cx + radius * cos1, cy + radius * sin1, z_hi]
        p3 = [cx + radius * cos0, cy + radius * sin0, z_hi]
        center_lo = [cx, cy, z_lo]
        center_hi = [cx, cy, z_hi]

        # Side
        triangles.append((p0, p1, p2))
        triangles.append((p0, p2, p3))
        # Bottom
        triangles.append((center_lo, p1, p0))
        # Top
        triangles.append((center_hi, p3, p2))

    return triangles


def box_mesh(x, y, z, dx, dy, dz):
    """Create a rectangular box from corner (x,y,z) with dimensions dx,dy,dz."""
    triangles = []
    # 8 vertices
    v = [
        [x,      y,      z],
        [x + dx, y,      z],
        [x + dx, y + dy, z],
        [x,      y + dy, z],
        [x,      y,      z + dz],
        [x + dx, y,      z + dz],
        [x + dx, y + dy, z + dz],
        [x,      y + dy, z + dz],
    ]
    # 6 faces, 2 triangles each
    faces = [
        (0, 1, 2, 3),  # bottom
        (4, 7, 6, 5),  # top
        (0, 4, 5, 1),  # front
        (2, 6, 7, 3),  # back
        (0, 3, 7, 4),  # left
        (1, 5, 6, 2),  # right
    ]
    for f in faces:
        triangles.append((v[f[0]], v[f[1]], v[f[2]]))
        triangles.append((v[f[0]], v[f[2]], v[f[3]]))
    return triangles


def triangles_to_stl(triangles, filename):
    """Convert list of triangle tuples to STL file."""
    n = len(triangles)
    m = mesh.Mesh(np.zeros(n, dtype=mesh.Mesh.dtype))
    for i, (v0, v1, v2) in enumerate(triangles):
        m.vectors[i][0] = v0
        m.vectors[i][1] = v1
        m.vectors[i][2] = v2
    m.save(filename)
    print(f"  Saved: {filename} ({n} triangles)")


# =============================================================================
# Part 1: Coil Form (Spool)
# =============================================================================

def generate_coil_form():
    """
    Spool for winding 20 turns of 24 AWG magnet wire at R = 50mm.

    Design:
    - Inner diameter: 96mm (wire center at ~50mm radius)
    - Winding channel width: 15mm (fits 20 turns single-layer with margin)
    - Winding channel depth: 2mm
    - Flange width: 2mm on each side
    - Total outer diameter: ~104mm
    - Height (along axis): 19mm (15mm channel + 2mm flanges)
    - 4 alignment holes on flanges for mounting rod (6mm dia)
    - Flat base section for standing upright

    Wire: 24 AWG insulated diameter ~0.559mm
    20 turns x 0.559mm = 11.2mm winding width, fits in 15mm channel
    """
    print("\nGenerating coil form...")

    # Dimensions (mm)
    r_inner = 48.0      # inner wall of channel (wire sits at ~50mm from center)
    r_channel = 50.0     # wire center radius
    r_outer = 52.0       # outer wall of channel
    channel_width = 15.0 # axial width of winding channel
    flange_h = 2.0       # flange thickness
    flange_r = 55.0      # flange outer radius

    total_height = channel_width + 2 * flange_h  # 19mm

    all_triangles = []

    # Bottom flange (full disc with hole)
    all_triangles.extend(cylinder_mesh(flange_r, r_inner, flange_h, 80, z_offset=0))

    # Channel walls (inner and outer, thinner)
    # Inner wall
    all_triangles.extend(cylinder_mesh(r_inner, r_inner - 2.0, total_height, 80, z_offset=0))
    # Outer wall
    all_triangles.extend(cylinder_mesh(r_outer + 2.0, r_outer, total_height, 80, z_offset=0))

    # Top flange
    all_triangles.extend(cylinder_mesh(flange_r, r_inner, flange_h, 80,
                                       z_offset=flange_h + channel_width))

    # Alignment rod holes (4x, at 90 degree intervals, on flanges)
    # These are represented as small cylinders that we'd subtract in a real
    # CAD tool. For STL, we'll add alignment pin sockets instead.
    # Add 4 alignment posts on top flange
    for angle in [0, np.pi/2, np.pi, 3*np.pi/2]:
        px = (flange_r - 3) * np.cos(angle)
        py = (flange_r - 3) * np.sin(angle)
        # Small post sticking up from top flange
        all_triangles.extend(solid_cylinder_mesh(
            2.0, 8.0, 16, z_offset=total_height, x_offset=px, y_offset=py))

    triangles_to_stl(all_triangles, 'coil_form.stl')
    print(f"  Coil form: ID={r_inner*2:.0f}mm, OD={flange_r*2:.0f}mm, "
          f"H={total_height:.0f}mm")
    print(f"  Channel: {channel_width:.0f}mm wide, fits 20 turns of 24 AWG")
    print(f"  Print 2 of these")


# =============================================================================
# Part 2: Sensor Positioning Rail
# =============================================================================

def generate_sensor_rail():
    """
    Linear rail for positioning Hall sensor along the coil axis.

    Design:
    - 120mm long rail (covers -5cm to +5cm from center, plus margin)
    - 10mm wide, 5mm tall base
    - Position marks every 5mm (notches on the edge)
    - Deeper marks every 10mm
    - Sensor holder clip at one end (slot for SS49E, 4.1mm wide)
    - Center mark (deeper notch)
    """
    print("\nGenerating sensor rail...")

    all_triangles = []

    rail_length = 140.0  # mm (extra margin beyond +/-5cm)
    rail_width = 12.0
    rail_height = 5.0

    # Main rail body
    all_triangles.extend(box_mesh(0, 0, 0, rail_length, rail_width, rail_height))

    # Position marks: notches every 5mm
    # Represented as small raised bumps (easier to print than notches)
    mark_width = 0.8
    mark_height = 1.5
    center_x = rail_length / 2.0

    for i in range(-10, 11):  # -50mm to +50mm in 5mm steps
        x_pos = center_x + i * 5.0 - mark_width / 2.0

        if i == 0:
            # Center mark -- taller and wider
            all_triangles.extend(box_mesh(
                x_pos - 0.4, 0, rail_height,
                mark_width + 0.8, rail_width, mark_height + 1.0))
        elif i % 2 == 0:
            # 10mm marks -- medium height
            all_triangles.extend(box_mesh(
                x_pos, 0, rail_height,
                mark_width, rail_width, mark_height))
        else:
            # 5mm marks -- short
            all_triangles.extend(box_mesh(
                x_pos, 0, rail_height,
                mark_width, rail_width * 0.5, mark_height * 0.6))

    # Sensor holder at the sliding end
    # SS49E is ~4.1mm wide, ~3mm thick, ~1.5mm legs
    # Create a clip that holds the sensor perpendicular to the rail
    holder_x = 5.0  # near the start of the rail
    holder_width = 8.0
    holder_height = 15.0

    # Back wall
    all_triangles.extend(box_mesh(
        holder_x, rail_width/2 - holder_width/2, rail_height,
        2.0, holder_width, holder_height))
    # Left wall
    all_triangles.extend(box_mesh(
        holder_x + 2.0, rail_width/2 - holder_width/2, rail_height,
        6.0, 1.5, holder_height))
    # Right wall
    all_triangles.extend(box_mesh(
        holder_x + 2.0, rail_width/2 + holder_width/2 - 1.5, rail_height,
        6.0, 1.5, holder_height))

    triangles_to_stl(all_triangles, 'sensor_rail.stl')
    print(f"  Rail: {rail_length:.0f}mm long, {rail_width:.0f}mm wide")
    print(f"  Marks every 5mm, center marked")
    print(f"  Sensor holder clip included")


# =============================================================================
# Part 3: Separation Spacers
# =============================================================================

def generate_spacers():
    """
    Spacer rings that set coil separation distance.

    3 sizes:
    - 45mm (0.9R) -- thickness = (45 - 19) / 2 = 13mm per spacer
    - 50mm (1.0R) -- thickness = (50 - 19) / 2 = 15.5mm per spacer
    - 55mm (1.1R) -- thickness = (55 - 19) / 2 = 18mm per spacer

    Wait -- the separation is center-to-center of the coil windings,
    not edge-to-edge of the forms. The coil form is 19mm tall,
    and the wire center is at the midpoint (9.5mm from each edge).

    So the spacer between the two forms sets the gap:
    gap = separation - form_height = sep - 19mm
    For sep = 50mm: gap = 31mm
    For sep = 45mm: gap = 26mm
    For sep = 55mm: gap = 36mm

    Actually, the separation is measured between wire centers.
    Wire center is at form midheight = 9.5mm from edge.
    So gap between form edges = separation - 2*0 = separation - 0
    No -- if forms touch, separation = 19mm (one form height).
    Need spacers that go between the alignment posts.

    Simpler: spacer height = desired separation - form_height
    and the spacer sits between the two forms on the alignment posts.

    sep = 50mm: spacer = 50 - 19 = 31mm
    sep = 45mm: spacer = 45 - 19 = 26mm
    sep = 55mm: spacer = 55 - 19 = 36mm
    """
    print("\nGenerating separation spacers...")

    form_height = 19.0  # mm (from coil form)

    # Spacer: tube that fits over the alignment posts (2mm radius posts)
    # Inner radius: 2.1mm (slight clearance over 2mm posts)
    # Outer radius: 4.5mm
    post_r_inner = 2.2
    post_r_outer = 4.5

    # Flange radius for the coil form alignment posts
    flange_r = 55.0

    for sep_mm, label in [(45, "0.9R"), (50, "1.0R"), (55, "1.1R")]:
        spacer_h = sep_mm - form_height
        if spacer_h <= 0:
            print(f"  WARNING: {label} spacer height would be {spacer_h}mm -- skipping")
            continue

        all_triangles = []

        # 4 spacer tubes at the same positions as alignment posts
        for angle in [0, np.pi/2, np.pi, 3*np.pi/2]:
            px = (flange_r - 3) * np.cos(angle)
            py = (flange_r - 3) * np.sin(angle)
            all_triangles.extend(cylinder_mesh(
                post_r_outer, post_r_inner, spacer_h, 24,
                z_offset=0))
            # Offset all triangles to post position
            for j in range(len(all_triangles) - 24*8, len(all_triangles)):
                v0, v1, v2 = all_triangles[j]
                all_triangles[j] = (
                    [v0[0] + px, v0[1] + py, v0[2]],
                    [v1[0] + px, v1[1] + py, v1[2]],
                    [v2[0] + px, v2[1] + py, v2[2]],
                )

        # Add a thin connecting ring for rigidity
        all_triangles.extend(cylinder_mesh(flange_r - 0.5, flange_r - 3.5,
                                           2.0, 80, z_offset=spacer_h/2 - 1))

        filename = f'spacer_{sep_mm}mm_{label.replace(".", "")}.stl'
        triangles_to_stl(all_triangles, filename)
        print(f"  {label} spacer: {spacer_h:.0f}mm height, "
              f"sets {sep_mm}mm center-to-center separation")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("HELMHOLTZ BENCH TEST -- 3D PRINT FILES")
    print("=" * 60)
    print("\nTarget printer: Bambu Lab A1/P1/X1")
    print("Material: PLA or PETG (non-magnetic)")
    print("All parts fit within 256x256mm bed")

    generate_coil_form()
    generate_sensor_rail()
    generate_spacers()

    print(f"\n{'=' * 60}")
    print("PRINT LIST")
    print(f"{'=' * 60}")
    print("  coil_form.stl          -- print QTY 2")
    print("  sensor_rail.stl        -- print QTY 1")
    print("  spacer_45mm_09R.stl    -- print QTY 1 (0.9R test)")
    print("  spacer_50mm_10R.stl    -- print QTY 1 (1.0R standard)")
    print("  spacer_55mm_11R.stl    -- print QTY 1 (1.1R test)")
    print("\nMaterial: PLA or PETG. Must be non-magnetic.")
    print("Layer height: 0.2mm is fine. No special settings needed.")
    print("Infill: 20% is sufficient for structural rigidity.")
