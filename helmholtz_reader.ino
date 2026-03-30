/*
  Helmholtz Coil Field Measurement
  =================================
  Reads SS49E Hall sensor via ADS1115 16-bit ADC.
  Takes 100 samples per measurement, reports mean and std dev.

  Wiring:
    ADS1115 VDD -> 5V
    ADS1115 GND -> GND
    ADS1115 SCL -> A5
    ADS1115 SDA -> A4
    ADS1115 A0  -> SS49E OUT (pin 3)
    SS49E VCC   -> 5V (pin 1)
    SS49E GND   -> GND (pin 2)

  Usage:
    Open Serial Monitor at 115200 baud.
    Type a z-position (in cm) and press Enter.
    The sketch takes 100 readings and prints the result.
    Type "zero" to take a zero-field baseline.
    Type "done" to print all data as CSV.

  Install library: Adafruit ADS1X15
    (Arduino IDE -> Library Manager -> search "Adafruit ADS1X15")
*/

#include <Wire.h>
#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads;

// Measurement storage
#define MAX_POINTS 30
float positions[MAX_POINTS];
float readings[MAX_POINTS];   // mean voltage (mV)
float noise[MAX_POINTS];      // std dev (mV)
int numPoints = 0;

float zeroBaseline = 0.0;     // zero-field baseline voltage (mV)
bool zeroSet = false;

const int SAMPLES = 100;      // samples per measurement point
const int SAMPLE_DELAY = 10;  // ms between samples

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  Serial.println(F("================================"));
  Serial.println(F("Helmholtz Coil Field Measurement"));
  Serial.println(F("================================"));

  if (!ads.begin()) {
    Serial.println(F("ERROR: ADS1115 not found. Check wiring."));
    while (1);
  }

  // Gain 1: +/- 4.096V range, 0.125 mV/bit
  ads.setGain(GAIN_ONE);

  Serial.println(F("ADS1115 ready. Gain: +/- 4.096V (0.125 mV/bit)"));
  Serial.println();
  Serial.println(F("Commands:"));
  Serial.println(F("  Type a number (z-position in cm) -> takes measurement"));
  Serial.println(F("  Type 'zero'  -> records zero-field baseline (do this first!)"));
  Serial.println(F("  Type 'done'  -> prints all data as CSV"));
  Serial.println(F("  Type 'clear' -> clears all data"));
  Serial.println();
  Serial.println(F("STEP 1: With coil current OFF, type 'zero' to set baseline."));
  Serial.println(F("STEP 2: Turn on coil current."));
  Serial.println(F("STEP 3: Position sensor, type z-position (e.g. '0' for center)."));
  Serial.println();
}

void takeMeasurement(float position) {
  if (numPoints >= MAX_POINTS) {
    Serial.println(F("ERROR: Max points reached. Type 'done' to export."));
    return;
  }

  Serial.print(F("Measuring at z = "));
  Serial.print(position, 1);
  Serial.print(F(" cm ... "));

  float sum = 0;
  float sumSq = 0;
  float values[SAMPLES];

  // Discard first few readings (settling)
  for (int i = 0; i < 5; i++) {
    ads.readADC_SingleEnded(0);
    delay(5);
  }

  // Take SAMPLES readings
  for (int i = 0; i < SAMPLES; i++) {
    int16_t raw = ads.readADC_SingleEnded(0);
    float mV = raw * 0.125;  // 0.125 mV per bit at GAIN_ONE
    values[i] = mV;
    sum += mV;
    delay(SAMPLE_DELAY);
  }

  float mean = sum / SAMPLES;

  // Compute std dev
  for (int i = 0; i < SAMPLES; i++) {
    sumSq += (values[i] - mean) * (values[i] - mean);
  }
  float stddev = sqrt(sumSq / (SAMPLES - 1));

  // Store
  positions[numPoints] = position;
  readings[numPoints] = mean;
  noise[numPoints] = stddev;
  numPoints++;

  // Print result
  float corrected = mean - zeroBaseline;
  Serial.print(F("raw="));
  Serial.print(mean, 3);
  Serial.print(F(" mV, baseline="));
  Serial.print(zeroBaseline, 3);
  Serial.print(F(" mV, signal="));
  Serial.print(corrected, 3);
  Serial.print(F(" mV, noise="));
  Serial.print(stddev, 3);
  Serial.println(F(" mV"));

  // Estimate field (rough, assuming ~1.4 mV/G sensitivity)
  float gauss_est = corrected / 1.4;
  float uT_est = gauss_est * 100.0;
  Serial.print(F("  Estimated field: ~"));
  Serial.print(uT_est, 0);
  Serial.println(F(" uT (approximate -- use relative values for validation)"));
  Serial.println();
}

void takeZero() {
  Serial.print(F("Taking zero-field baseline (100 samples)... "));

  float sum = 0;
  for (int i = 0; i < 5; i++) {
    ads.readADC_SingleEnded(0);
    delay(5);
  }
  for (int i = 0; i < SAMPLES; i++) {
    int16_t raw = ads.readADC_SingleEnded(0);
    sum += raw * 0.125;
    delay(SAMPLE_DELAY);
  }

  zeroBaseline = sum / SAMPLES;
  zeroSet = true;

  Serial.print(F("baseline = "));
  Serial.print(zeroBaseline, 3);
  Serial.println(F(" mV"));
  Serial.println(F("Baseline set. Now turn on coil current and begin measuring."));
  Serial.println();
}

void printCSV() {
  Serial.println();
  Serial.println(F("=== CSV DATA (copy everything below this line) ==="));
  Serial.println(F("z_cm,raw_mV,signal_mV,noise_mV,B_B_center"));

  // Find center reading (position closest to 0)
  float centerSignal = 0;
  for (int i = 0; i < numPoints; i++) {
    if (abs(positions[i]) < 0.1) {
      centerSignal = readings[i] - zeroBaseline;
      break;
    }
  }
  if (centerSignal == 0 && numPoints > 0) {
    centerSignal = readings[0] - zeroBaseline;  // fallback
  }

  for (int i = 0; i < numPoints; i++) {
    float signal = readings[i] - zeroBaseline;
    float normalized = (centerSignal != 0) ? signal / centerSignal : 0;

    Serial.print(positions[i], 1);
    Serial.print(F(","));
    Serial.print(readings[i], 3);
    Serial.print(F(","));
    Serial.print(signal, 3);
    Serial.print(F(","));
    Serial.print(noise[i], 3);
    Serial.print(F(","));
    Serial.println(normalized, 4);
  }

  Serial.println(F("=== END CSV ==="));
  Serial.println();
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.equalsIgnoreCase("zero")) {
      takeZero();
    } else if (input.equalsIgnoreCase("done")) {
      printCSV();
    } else if (input.equalsIgnoreCase("clear")) {
      numPoints = 0;
      zeroBaseline = 0;
      zeroSet = false;
      Serial.println(F("All data cleared."));
    } else {
      // Try to parse as a number (z-position)
      float pos = input.toFloat();
      if (input.length() > 0 && (pos != 0 || input == "0" || input == "0.0")) {
        if (!zeroSet) {
          Serial.println(F("WARNING: Zero baseline not set! Type 'zero' first with current OFF."));
        }
        takeMeasurement(pos);
      } else {
        Serial.println(F("Unknown command. Type a number, 'zero', 'done', or 'clear'."));
      }
    }
  }
}
