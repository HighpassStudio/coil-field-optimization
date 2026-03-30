# Helmholtz Coil Bench Test -- Step by Step Manual

Print this document. Follow each step in order. Check the box when done.

---

## PHASE 1: PRINT & PREP (before parts arrive)

- [ ] **1.1** Run `python generate_stl.py` in the coil-field-optimization folder
- [ ] **1.2** Load `coil_form.stl` in Bambu Studio. Print **2 copies**. PLA, 20% infill, 0.2mm layers.
- [ ] **1.3** Print `sensor_rail.stl` -- **1 copy**
- [ ] **1.4** Print `spacer_50mm_10R.stl` -- **1 copy** (start with standard Helmholtz)
- [ ] **1.5** Print `spacer_45mm_09R.stl` and `spacer_55mm_11R.stl` -- **1 each** (for later tests)

---

## PHASE 2: WIND THE COILS (when wire arrives)

- [ ] **2.1** Cut two equal lengths of 24 AWG magnet wire. Each coil needs ~6.5 meters (20 turns x 31.4 cm/turn + 30 cm lead on each end).
- [ ] **2.2** Sand the last 1 cm of each wire end with fine sandpaper to remove enamel insulation. The enamel must be removed for electrical contact.
- [ ] **2.3** Wind **Coil A**: Feed wire through the channel on coil form #1. Wind 20 turns tightly, single layer, all in the same direction. Count carefully. Secure ends with tape.
- [ ] **2.4** Wind **Coil B**: Same as Coil A on form #2. **Same winding direction.** This is critical -- if the coils are wound opposite, the fields cancel instead of adding.
- [ ] **2.5** Connect the two coils **in series**: solder or twist the end of Coil A to the start of Coil B. You should have 2 free leads total (start of A, end of B).

---

## PHASE 3: RESISTANCE CHECK

- [ ] **3.1** Set multimeter to resistance (ohms) mode.
- [ ] **3.2** Measure resistance between the two free leads.
- [ ] **3.3** Write down: _______ ohms
- [ ] **3.4** Expected: ~1.0 ohm. Acceptable range: 0.8 to 1.3 ohm. If outside this range, check for bad solder joints or shorted turns.
- [ ] **3.5** Record ambient temperature: _______ C

---

## PHASE 4: WIRE THE ELECTRONICS

### Parts needed: Arduino Nano, ADS1115 module, SS49E sensor, breadboard, jumper wires

- [ ] **4.1** Install the Arduino IDE on your computer if not already installed.
- [ ] **4.2** Install the CH340 driver if using an Arduino clone.
- [ ] **4.3** In Arduino IDE, go to **Tools > Manage Libraries**, search "Adafruit ADS1X15", install it.
- [ ] **4.4** Open `helmholtz_reader.ino` from the coil-field-optimization folder.
- [ ] **4.5** Select board: **Tools > Board > Arduino Nano**
- [ ] **4.6** Select processor: **ATmega328P (Old Bootloader)** if upload fails with the default.
- [ ] **4.7** Upload the sketch.
- [ ] **4.8** Wire the circuit on the breadboard:

```
ADS1115 VDD  --> Arduino 5V
ADS1115 GND  --> Arduino GND
ADS1115 SCL  --> Arduino A5
ADS1115 SDA  --> Arduino A4
ADS1115 A0   --> SS49E pin 3 (Output)

SS49E pin 1  --> Arduino 5V  (leftmost pin, flat side facing you)
SS49E pin 2  --> Arduino GND (center pin)
SS49E pin 3  --> ADS1115 A0  (rightmost pin)
```

- [ ] **4.9** Open Serial Monitor: **Tools > Serial Monitor**, set baud to **115200**.
- [ ] **4.10** You should see: "Helmholtz Coil Field Measurement" and "ADS1115 ready."
- [ ] **4.11** If you see "ERROR: ADS1115 not found" -- check SDA/SCL wiring.

---

## PHASE 5: ASSEMBLE THE TEST RIG

- [ ] **5.1** Stack the coils: Coil A (bottom) --> 1.0R spacer --> Coil B (top). Align using the 4 posts on each form.
- [ ] **5.2** Verify separation with calipers: measure center-to-center distance between the middle of each winding channel. Should be **50.0 mm +/- 1 mm**.
- [ ] **5.3** Place the sensor rail through the center of the coil assembly, along the axis (the z-axis). The rail should pass through the holes in the coil forms.
- [ ] **5.4** The SS49E sensor should be mounted in the clip on the rail, with the flat face perpendicular to the axis.
- [ ] **5.5** Connect the coil leads to the bench power supply. Red to +, black to -.
- [ ] **5.6** Set the power supply to **CC mode** (constant current).
- [ ] **5.7** Set current limit to **0.0 A** (start with zero).
- [ ] **5.8** Turn on the power supply (current still at 0).

---

## PHASE 6: TAKE ZERO-FIELD BASELINE

- [ ] **6.1** With the power supply current at 0.0 A, type `zero` in Serial Monitor and press Enter.
- [ ] **6.2** Wait for "Baseline set" message.
- [ ] **6.3** Write down baseline voltage: _______ mV

---

## PHASE 7: TEST 1 -- CENTER FIELD vs CURRENT (Linearity)

- [ ] **7.1** Position the sensor at the center mark on the rail (z = 0 cm).
- [ ] **7.2** Set current to **0.5 A**. Wait 5 seconds for stabilization.
- [ ] **7.3** Type `0` in Serial Monitor, press Enter. Record the signal_mV value.
- [ ] **7.4** Set current to **1.0 A**. Wait 5 seconds.
- [ ] **7.5** Type `0` in Serial Monitor, press Enter. Record.
- [ ] **7.6** Set current to **1.5 A**. Wait 5 seconds.
- [ ] **7.7** Type `0` in Serial Monitor, press Enter. Record.
- [ ] **7.8** Set current back to **0.0 A**.

Results:

| Current (A) | Signal (mV) |
|-------------|-------------|
| 0.5 | _______ |
| 1.0 | _______ |
| 1.5 | _______ |

**Check:** Signal at 1.0A should be ~2x signal at 0.5A. Signal at 1.5A should be ~3x signal at 0.5A. If not linear, check wiring or current regulation.

---

## PHASE 8: TEST 2 -- AXIAL PROFILE at 1.0R SEPARATION

- [ ] **8.1** Type `clear` in Serial Monitor to reset data.
- [ ] **8.2** Type `zero` to re-take baseline (current at 0 A).
- [ ] **8.3** Set current to **1.0 A**.
- [ ] **8.4** For each position below, slide the sensor to that mark on the rail, wait 3 seconds, then type the z-position and press Enter:

| Step | Position | Type this |
|------|----------|-----------|
| a | -4 cm mark | `-4` |
| b | -3 cm mark | `-3` |
| c | -2 cm mark | `-2` |
| d | -1 cm mark | `-1` |
| e | Center (0) | `0` |
| f | +1 cm mark | `1` |
| g | +2 cm mark | `2` |
| h | +3 cm mark | `3` |
| i | +4 cm mark | `4` |

- [ ] **8.5** After all 9 points, type `done` to get the CSV output.
- [ ] **8.6** Copy the entire CSV block from Serial Monitor.
- [ ] **8.7** Set current to **0.0 A**.

---

## PHASE 9: TEST 3 -- SEPARATION COMPARISON

### 9A: Test at 0.9R (4.5 cm separation)

- [ ] **9A.1** Disassemble the coil stack.
- [ ] **9A.2** Replace the 1.0R spacer with the **0.9R spacer (45mm)**.
- [ ] **9A.3** Reassemble. Verify separation: **45.0 mm** with calipers.
- [ ] **9A.4** Type `clear` then `zero` (current at 0).
- [ ] **9A.5** Set current to 1.0 A.
- [ ] **9A.6** Repeat the 9-point axial scan (steps 8.4a through 8.4i).
- [ ] **9A.7** Type `done` and copy CSV.

### 9B: Test at 1.1R (5.5 cm separation)

- [ ] **9B.1** Replace spacer with the **1.1R spacer (55mm)**.
- [ ] **9B.2** Verify separation: **55.0 mm** with calipers.
- [ ] **9B.3** Type `clear` then `zero`.
- [ ] **9B.4** Set current to 1.0 A.
- [ ] **9B.5** Repeat 9-point axial scan.
- [ ] **9B.6** Type `done` and copy CSV.

---

## PHASE 10: REPEAT FOR CONFIDENCE

- [ ] **10.1** Go back to 1.0R separation.
- [ ] **10.2** Repeat Phase 8 (full axial scan) two more times.
- [ ] **10.3** You should now have 3 independent runs at 1.0R, plus 1 each at 0.9R and 1.1R.

---

## PHASE 11: SEND DATA FOR VALIDATION

Take photos and send me:

1. **Photo** of the assembled coil rig with calipers showing separation
2. **Photo** of the multimeter showing coil resistance
3. **All CSV outputs** from the Serial Monitor (paste as text)
4. **Photo** of the wiring on the breadboard

I will:
- Compare your measured normalized profile against the simulation prediction
- Check linearity
- Verify the separation ranking (1.0R should be flattest)
- Tell you if the model is validated or needs debugging

---

## QUICK REFERENCE: Serial Monitor Commands

| Command | What it does |
|---------|-------------|
| `zero` | Takes 100-sample zero-field baseline (do first, current OFF) |
| A number (e.g. `0`, `-3`, `2.5`) | Takes measurement at that z-position (cm) |
| `done` | Prints all data as CSV (copy this) |
| `clear` | Erases all stored data |

---

## TROUBLESHOOTING

**"ADS1115 not found"**
- Check SDA (A4) and SCL (A5) connections
- Make sure ADS1115 VDD is connected to 5V, not 3.3V

**Readings don't change when current changes**
- Sensor may be backwards. Flip it 180 degrees.
- Check that sensor pin 3 goes to ADS1115 A0 input

**Very noisy readings (noise > 5% of signal)**
- Move sensor wires away from coil leads
- Use shorter jumper wires
- Check that power supply is in CC mode (not CV)
- Add a 0.1 uF capacitor between sensor VCC and GND (right at the sensor)

**Signal is negative**
- Earth's field may be opposing your coil field. This is normal.
- The normalized B/B_center values will still be correct.

**All readings are the same**
- Sensor might be saturated. Check that total field < 1000 Gauss (100 mT).
- At 1A with 20 turns, center field should be ~360 uT = 3.6 Gauss. Well within range.
