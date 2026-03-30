# Amazon Shopping List -- Helmholtz Bench Build

Order these items. Search URLs provided for each.

---

## Required Items

### 1. Magnet Wire -- 24 AWG Enameled Copper (~100 ft)
- **Search:** [24 AWG magnet wire enameled copper Remington Industries](https://www.amazon.com/s?k=24+AWG+magnet+wire+enameled+copper+Remington+Industries)
- **Price:** $8-15
- **Notes:** Get the 1/4 lb spool (~99 ft). Must be enameled, not bare. Avoid "bondable" wire.

### 2. Hall Effect Sensor -- SS49E Linear (pack of 5-10)
- **Search:** [SS49E linear Hall effect sensor](https://www.amazon.com/s?k=SS49E+linear+Hall+effect+sensor)
- **Price:** $5-9
- **Notes:** AH49E or OH49E are equivalent. Verify pinout before wiring (pin 1=VCC, 2=GND, 3=OUT, flat side facing you).

### 3. ADS1115 16-bit ADC Module (pack of 2-3)
- **Search:** [ADS1115 16 bit ADC module I2C Arduino](https://www.amazon.com/s?k=ADS1115+16+bit+ADC+module+I2C+Arduino)
- **Price:** $6-12
- **Warning:** Do NOT buy ADS1015 (12-bit). They look identical. Check the listing title carefully.

### 4. Arduino Nano (clone is fine)
- **Search:** [Arduino Nano V3 ATmega328P CH340](https://www.amazon.com/s?k=Arduino+Nano+V3+ATmega328P+CH340)
- **Price:** $4-8
- **Notes:** Get one with pre-soldered headers for breadboard use. Install CH340 driver on Windows.

### 5. DC Bench Power Supply -- 30V 5A with CC mode
- **Search:** [adjustable DC bench power supply 30V 5A](https://www.amazon.com/s?k=adjustable+DC+bench+power+supply+30V+5A)
- **Price:** $35-50
- **Notes:** LongWei LW-K3010D or NICE-POWER SPS3010 are good budget options. Must have CC (constant current) mode. Switching supply is fine for this application.

### 6. Digital Calipers -- 6 inch stainless steel
- **Search:** [digital calipers stainless steel 6 inch](https://www.amazon.com/s?k=digital+calipers+stainless+steel+6+inch)
- **Price:** $10-15
- **Notes:** Neiko 01407A is a solid budget option. Avoid plastic-body calipers.

### 7. Breadboard + Jumper Wire Kit
- **Search:** [breadboard jumper wire kit Arduino](https://www.amazon.com/s?k=breadboard+jumper+wire+kit+Arduino)
- **Price:** $8-15
- **Notes:** Need male-to-male AND male-to-female jumpers. ELEGOO or REXQualis kits include both.

---

## Already Have? Skip These

- If you already have an Arduino, skip #4
- If you already have a bench power supply with CC mode, skip #5
- If you already have calipers, skip #6
- If you already have a breadboard + wires, skip #7

## Estimated Total

- **Minimum (have Arduino + supply + calipers + breadboard):** $20-35
- **Full build from scratch:** $75-115

## 3D Print Files (no purchase needed)

Run `python generate_stl.py` to generate:
- `coil_form.stl` -- print QTY 2
- `sensor_rail.stl` -- print QTY 1
- `spacer_45mm_09R.stl` -- print QTY 1
- `spacer_50mm_10R.stl` -- print QTY 1
- `spacer_55mm_11R.stl` -- print QTY 1

Material: PLA or PETG (non-magnetic). 20% infill, 0.2mm layer height.
