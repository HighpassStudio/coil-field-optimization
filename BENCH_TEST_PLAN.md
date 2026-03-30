# Bench Test Plan: Helmholtz Baseline Validation

**Goal:** Prove that a physical Helmholtz pair matches the simulation within 10%, validating the entire optimization framework.

---

## Bill of Materials

| Item | Spec | Source | Est. Cost |
|------|------|--------|-----------|
| Magnet wire | 24 AWG, 50 ft minimum | Amazon/eBay (remington industries) | $8-12 |
| Hall effect sensor | SS49E linear (or AH49E) | Amazon/eBay | $3-5 for 5 pack |
| Arduino Nano or Uno | Any clone works | Amazon | $5-10 |
| Bench power supply | 0-2A adjustable, CC mode | Amazon (or existing) | $25-40 |
| Multimeter | For resistance check | Existing | $0 |
| 3D printed coil forms | 5 cm radius, 2 needed | Print yourself or order | $2-5 filament |
| Ruler / calipers | For positioning | Existing | $0 |
| Jumper wires, breadboard | Sensor hookup | Existing or $5 | $0-5 |
| ADS1115 16-bit ADC module | Required -- Arduino 10-bit is inadequate | Amazon | $3-5 |
| Calipers or printed slide | Sensor positioning (+/- 0.5 mm) | Existing or Amazon | $0-15 |

**Total: $45-90** (less if you have a power supply and Arduino)

---

## Coil Build Spec

```
Radius:          5.0 cm (50 mm)
Turns per coil:  20
Wire:            24 AWG magnet wire (0.511 mm bare)
Coils:           2 identical
Separations:     4.5 cm (0.9R), 5.0 cm (1.0R), 5.5 cm (1.1R)
```

### Coil Form Design

3D print two identical forms:
- Inner diameter: 100 mm (for R = 50 mm to coil center)
- Channel width: ~15 mm (fits 20 turns single-layer with margin)
- Channel depth: ~2 mm
- Include alignment tabs or slots for a rail/rod to set separation

OR: wind on any 100 mm diameter cylinder (PVC pipe, jar, etc.)

### Winding Notes

- Wind all turns in the same direction on both coils
- Keep turns tight and in a single layer if possible
- Mark the start/end leads clearly
- Both coils wired in series (same current guaranteed)
- Total resistance should measure ~1.0 ohm with a multimeter

---

## Sensor Setup

### SS49E Hall Sensor

- Linear output: ~1.0 mV/Gauss (1 Gauss = 100 uT)
- At 360 uT (center field at 1A): expect ~3.6 mV change from quiescent
- Quiescent voltage: ~2.5V (at 5V supply)
- Sensitivity: adequate for expected field range (170-570 uT)

### ADC -- Use ADS1115 (Required)

The Arduino's built-in 10-bit ADC is inadequate. At 4.88 mV/count on a 5V
reference, the ~5 mV signal from 3.6 Gauss is barely 1 count. Even with
the internal 1.1V reference (1.07 mV/count), resolution is marginal for
detecting the small variations between separation configurations.

**Use an ADS1115 16-bit ADC module ($3-5):**
- Resolution: 0.125 mV/count at +/-4.096V gain
- At +/-0.256V gain: 0.0078 mV/count -- more than enough
- I2C interface, trivial Arduino library (Adafruit_ADS1X15)
- This is not optional -- the 10-bit ADC will produce noisy garbage

### Averaging

Take **100 samples per measurement point** and report the mean.
This reduces random noise by 10x (sqrt(100)).
Record the standard deviation of the 100 samples as your per-point
noise estimate. If std_dev > 5% of mean signal, investigate EMI sources.

### Wiring (ADS1115)

```
ADS1115 VDD   -> Arduino 5V
ADS1115 GND   -> Arduino GND
ADS1115 SCL   -> Arduino A5 (SCL)
ADS1115 SDA   -> Arduino A4 (SDA)
ADS1115 A0    -> SS49E pin 3 (Out)
SS49E pin 1   -> Arduino 5V
SS49E pin 2   -> Arduino GND
```

### Calibration

The SS49E sensitivity varies unit to unit (~1.0-1.75 mV/G, typically ~1.4 mV/G).
Calibrate against a known field or use relative measurements only.
For this test, **relative measurements (B/B_center) are sufficient**
to validate profile shape and separation comparison.

### Known Systematics

- **Earth's field (~0.5 G):** Subtract zero-current baseline reading at each
  position. Earth's field is ~uniform over the coil volume, so it shifts all
  readings by a constant offset that cancels in normalization.
- **Sensor self-heating:** SS49E dissipates ~15 mW. Allow 30 seconds thermal
  stabilization before recording.
- **EMI from power supply:** Use a linear bench supply in CC mode, not a
  switching supply. Keep sensor wires short and away from coil leads.
- **Coil symmetry:** If possible, measure each coil individually (disconnect
  one) to verify they produce similar center fields. Mismatch > 5% indicates
  a winding error.

---

## Measurement Protocol

### Test 1: Resistance Check

1. Measure total series resistance of both coils with multimeter
2. Expected: ~1.03 ohm at 20C
3. Record ambient temperature (resistance increases ~0.4%/C)

### Test 2: Center Field vs Current (Linearity)

1. Place Hall sensor at geometric center (z=0, on axis)
2. Set separation to 5.0 cm (1.0R)
3. Measure sensor output at: 0A, 0.5A, 1.0A, 1.5A
4. Subtract zero-current reading (Earth's field + offset)
5. Plot voltage vs current -- should be linear

**Pass criteria:** R^2 > 0.99

### Test 3: Axial Profile at 1.0R Separation

1. Set separation to 5.0 cm
2. Set current to 1.0 A
3. Measure Hall sensor output at z = -4, -3, -2, -1, 0, +1, +2, +3, +4 cm
4. Position sensor along the axis using the rail with cm markings
5. Record raw ADC values, subtract zero-field baseline
6. Normalize all readings to the center (z=0) value

**Predicted normalized values at 1.0R (from bench_predictions.py):**

| z (cm) | B/B_center predicted |
|--------|---------------------|
| -4.0 | 0.7724 |
| -3.0 | 0.9011 |
| -2.0 | 0.9754 |
| -1.0 | 0.9982 |
| 0.0 | 1.0000 |
| +1.0 | 0.9982 |
| +2.0 | 0.9754 |
| +3.0 | 0.9011 |
| +4.0 | 0.7724 |

**Pass criteria:** All measured ratios within 5% of predicted

### Test 4: Separation Comparison (The Key Test)

1. Repeat Test 3 at separations: 4.5 cm (0.9R), 5.0 cm (1.0R), 5.5 cm (1.1R)
2. For each separation, compute the standard deviation of the 9-point profile
3. Compare non-uniformity ranking

**Predicted ranking (best to worst):**
1. 1.0R -- flattest profile (non-uniformity 0.169%)
2. 0.9R -- peaked in center (non-uniformity 0.347%)
3. 1.1R -- dipped in center (non-uniformity 0.432%)

**Pass criteria:** Measured ranking matches predicted ranking (1.0R is best)

### Test 5: Repeat for Confidence

1. Remove and re-seat the sensor
2. Repeat Tests 2-4
3. Record 3 independent runs minimum
4. Report mean +/- std dev for all measurements

---

## Predicted Values Summary (1.0 A, Standard Helmholtz)

```
Center field:       359.7 uT  (3.597 Gauss)
Coil resistance:    1.029 ohm
Power dissipation:  1.029 W
```

---

## What Success Looks Like

| Milestone | Criteria | Confidence Level |
|-----------|----------|-----------------|
| Resistance matches | Within 20% of 1.03 ohm | High -- just wire length |
| Field scales linearly | R^2 > 0.99 | High -- Biot-Savart is linear |
| Center field magnitude | Within 10% of 360 uT | Medium -- sensor calibration matters |
| Profile shape matches | Normalized values within 5% | Medium-high |
| Separation ranking correct | 1.0R beats 0.9R and 1.1R | **This is the key result** |

If all five pass, the model is validated and non-Helmholtz optimization work is justified.

---

## Data Recording Template

```
Date:
Ambient temp (C):
Coil resistance (ohm):
Sensor: SS49E / ADS1115 / other
ADC reference voltage:
Zero-field ADC reading:

Separation: ___ cm (___ R)
Current (A) | z (cm) | Raw ADC | Corrected | B/B_center
0.5         | 0      |         |           |
1.0         | 0      |         |           |
1.5         | 0      |         |           |
1.0         | -4     |         |           |
1.0         | -3     |         |           |
1.0         | -2     |         |           |
1.0         | -1     |         |           |
1.0         | 0      |         |           |
1.0         | +1     |         |           |
1.0         | +2     |         |           |
1.0         | +3     |         |           |
1.0         | +4     |         |           |
```
